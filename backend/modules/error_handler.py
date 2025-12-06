"""
Error handling and validation module.
Provides retry logic, rate limiting, better error messages, and code validation.
"""
import time
import traceback
from typing import Optional, Callable, Any, Dict, List, Tuple
from functools import wraps
import ast
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta


class RetryableError(Exception):
    """Exception that can be retried."""
    pass


class RateLimitExceeded(Exception):
    """Rate limit exceeded exception."""
    pass


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    retryable_exceptions: Tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay on each retry
        max_delay: Maximum delay between retries
        retryable_exceptions: Tuple of exceptions that should trigger retry
        on_retry: Optional callback function called on each retry
    
    Example:
        @retry_with_backoff(max_retries=3)
        def call_api():
            # API call that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        if on_retry:
                            on_retry(attempt + 1, max_retries, delay, e)
                        else:
                            print(f"[retry] Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}")
                            print(f"[retry] Retrying in {delay:.2f}s...")
                        
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        # Final attempt failed
                        print(f"[retry] All {max_retries + 1} attempts failed")
                        raise e
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


class RateLimiter:
    """
    Rate limiter using token bucket algorithm.
    """
    def __init__(self, max_requests: int, time_window: float):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> Tuple[bool, Optional[str]]:
        """
        Check if request is allowed.
        
        Args:
            identifier: Unique identifier for the rate limit (e.g., IP address, user ID)
        
        Returns:
            Tuple of (is_allowed, error_message)
        """
        now = time.time()
        
        # Clean old requests outside time window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < self.time_window
        ]
        
        # Check if limit exceeded
        if len(self.requests[identifier]) >= self.max_requests:
            oldest_request = min(self.requests[identifier])
            retry_after = self.time_window - (now - oldest_request)
            error_msg = f"Rate limit exceeded. Try again in {retry_after:.1f} seconds."
            return False, error_msg
        
        # Record request
        self.requests[identifier].append(now)
        return True, None
    
    def reset(self, identifier: Optional[str] = None):
        """Reset rate limit for identifier or all identifiers."""
        if identifier:
            self.requests[identifier] = []
        else:
            self.requests.clear()


# Global rate limiters
_rate_limiters: Dict[str, RateLimiter] = {}


def get_rate_limiter(limiter_name: str, max_requests: int, time_window: float) -> RateLimiter:
    """Get or create a rate limiter."""
    if limiter_name not in _rate_limiters:
        _rate_limiters[limiter_name] = RateLimiter(max_requests, time_window)
    return _rate_limiters[limiter_name]


def rate_limit(
    limiter_name: str,
    max_requests: int = 100,
    time_window: float = 60.0,
    get_identifier: Optional[Callable] = None
):
    """
    Decorator for rate limiting endpoints.
    
    Args:
        limiter_name: Name of the rate limiter
        max_requests: Maximum requests per time window
        time_window: Time window in seconds
        get_identifier: Function to get identifier from request (default: uses IP address)
    
    Example:
        @rate_limit("api", max_requests=100, time_window=60)
        def api_endpoint():
            pass
    """
    limiter = get_rate_limiter(limiter_name, max_requests, time_window)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get identifier (default: use IP from Flask request if available)
            identifier = "default"
            try:
                from flask import request
                if get_identifier:
                    identifier = get_identifier(request)
                else:
                    identifier = request.remote_addr or "unknown"
            except:
                # Flask not available or not in request context
                identifier = "default"
            
            is_allowed, error_msg = limiter.is_allowed(identifier)
            if not is_allowed:
                from flask import jsonify
                raise RateLimitExceeded(error_msg)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_code_syntax(code: str, language: str = "python") -> Tuple[bool, Optional[str]]:
    """
    Validate code syntax for various languages.
    
    Args:
        code: Code string to validate
        language: Programming language (python, javascript, typescript, etc.)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not code or not code.strip():
        return False, "Code is empty"
    
    language = language.lower()
    
    if language == "python":
        return _validate_python_syntax(code)
    elif language in ["javascript", "typescript", "js", "ts"]:
        return _validate_javascript_syntax(code)
    elif language == "json":
        return _validate_json_syntax(code)
    else:
        # For other languages, do basic validation (non-empty, no obvious syntax errors)
        # Can be extended later
        return True, None


def _validate_python_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """Validate Python syntax."""
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        error_msg = f"Python syntax error at line {e.lineno}: {e.msg}"
        if e.text:
            error_msg += f"\n  {e.text.strip()}"
            if e.offset:
                error_msg += f"\n  {' ' * (e.offset - 1)}^"
        return False, error_msg
    except Exception as e:
        return False, f"Python validation error: {str(e)}"


def _validate_javascript_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """Validate JavaScript/TypeScript syntax using node (if available)."""
    try:
        # Try using node to check syntax
        process = subprocess.run(
            ["node", "--check"],
            input=code,
            text=True,
            capture_output=True,
            timeout=5
        )
        if process.returncode == 0:
            return True, None
        else:
            error_output = process.stderr.strip() if process.stderr else "Unknown syntax error"
            return False, f"JavaScript syntax error: {error_output}"
    except FileNotFoundError:
        # Node.js not available, skip validation
        return True, None
    except subprocess.TimeoutExpired:
        return False, "JavaScript validation timed out"
    except Exception as e:
        # If validation fails due to system issues, don't block
        return True, None  # Allow code through if we can't validate


def _validate_json_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """Validate JSON syntax."""
    import json
    try:
        json.loads(code)
        return True, None
    except json.JSONDecodeError as e:
        return False, f"JSON syntax error at line {e.lineno}, column {e.colno}: {e.msg}"
    except Exception as e:
        return False, f"JSON validation error: {str(e)}"


def format_error_message(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    include_traceback: bool = False
) -> Dict[str, Any]:
    """
    Format error message with context and suggestions.
    
    Args:
        error: Exception that occurred
        context: Additional context (endpoint, parameters, etc.)
        include_traceback: Whether to include traceback
    
    Returns:
        Formatted error dictionary
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    # Base error response
    error_response = {
        "ok": False,
        "error": error_message,
        "error_type": error_type
    }
    
    # Add context if provided
    if context:
        error_response["context"] = context
    
    # Add traceback if requested (for debugging)
    if include_traceback:
        error_response["traceback"] = traceback.format_exc()
    
    # Add suggestions based on error type
    suggestions = _get_error_suggestions(error_type, error_message)
    if suggestions:
        error_response["suggestions"] = suggestions
    
    # Add retry information if applicable
    if isinstance(error, RateLimitExceeded):
        error_response["retry_after"] = _extract_retry_after(error_message)
    
    return error_response


def _get_error_suggestions(error_type: str, error_message: str) -> List[str]:
    """Get helpful suggestions based on error type."""
    suggestions = []
    
    error_type_lower = error_type.lower()
    error_msg_lower = error_message.lower()
    
    if "connection" in error_msg_lower or "timeout" in error_msg_lower:
        suggestions.extend([
            "Check your internet connection",
            "Verify the API endpoint is accessible",
            "Try again in a few moments"
        ])
    elif "rate limit" in error_msg_lower:
        suggestions.extend([
            "Wait a few seconds before trying again",
            "Reduce the frequency of your requests"
        ])
    elif "not found" in error_msg_lower or "404" in error_msg_lower:
        suggestions.extend([
            "Check if the repository path is correct",
            "Ensure the repository is indexed first"
        ])
    elif "syntax" in error_msg_lower:
        suggestions.extend([
            "Check the generated code for syntax errors",
            "Review the code formatting"
        ])
    elif "authentication" in error_msg_lower or "unauthorized" in error_msg_lower:
        suggestions.extend([
            "Check your API key is set correctly",
            "Verify API key has required permissions"
        ])
    elif "timeout" in error_msg_lower:
        suggestions.extend([
            "The request took too long",
            "Try with a smaller codebase or simpler query",
            "Check server logs for more details"
        ])
    
    return suggestions


def _extract_retry_after(error_message: str) -> Optional[float]:
    """Extract retry_after time from error message."""
    import re
    match = re.search(r'Try again in ([\d.]+) seconds?', error_message)
    if match:
        return float(match.group(1))
    return None


def graceful_degradation(fallback_value: Any = None, fallback_func: Optional[Callable] = None):
    """
    Decorator for graceful degradation when services fail.
    
    Args:
        fallback_value: Value to return if function fails
        fallback_func: Function to call if main function fails
    
    Example:
        @graceful_degradation(fallback_value=[])
        def get_search_results():
            # Search that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"[graceful_degradation] {func.__name__} failed: {str(e)}")
                print(f"[graceful_degradation] Using fallback")
                
                if fallback_func:
                    return fallback_func(*args, **kwargs)
                else:
                    return fallback_value
        
        return wrapper
    return decorator


def handle_errors(
    include_traceback: bool = False,
    retry_on_failure: bool = False,
    max_retries: int = 3
):
    """
    Decorator for error handling in Flask endpoints.
    
    Args:
        include_traceback: Include traceback in error response (for debugging)
        retry_on_failure: Automatically retry on failure
        max_retries: Maximum retries if retry_on_failure is True
    
    Example:
        @app.post("/endpoint")
        @handle_errors()
        def my_endpoint():
            # Endpoint code
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            from flask import request, jsonify
            
            try:
                # Wrap with retry if requested
                if retry_on_failure:
                    retry_func = retry_with_backoff(max_retries=max_retries)(func)
                    return retry_func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            
            except RateLimitExceeded as e:
                error_response = format_error_message(
                    e,
                    context={"endpoint": request.endpoint},
                    include_traceback=include_traceback
                )
                return jsonify(error_response), 429  # Too Many Requests
            
            except Exception as e:
                error_response = format_error_message(
                    e,
                    context={
                        "endpoint": request.endpoint,
                        "method": request.method
                    },
                    include_traceback=include_traceback
                )
                status_code = 500
                
                # Set appropriate status codes
                if "not found" in str(e).lower() or "404" in str(e).lower():
                    status_code = 404
                elif "unauthorized" in str(e).lower() or "authentication" in str(e).lower():
                    status_code = 401
                elif "bad request" in str(e).lower() or "invalid" in str(e).lower():
                    status_code = 400
                
                return jsonify(error_response), status_code
        
        return wrapper
    return decorator


# Helper function for validating generated code in endpoints
def validate_generated_code(code: str, language: str = "python", raise_on_error: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate generated code and optionally raise exception.
    
    Args:
        code: Generated code to validate
        language: Programming language
        raise_on_error: Whether to raise exception on validation failure
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    is_valid, error_message = validate_code_syntax(code, language)
    
    if not is_valid and raise_on_error:
        raise ValueError(f"Generated code validation failed: {error_message}")
    
    return is_valid, error_message


import os
from openai import OpenAI
from typing import Optional, List, Dict
from backend.config import (
    LLM_PROVIDER, LLM_MODEL,
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL,
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
    QWEN_API_KEY, QWEN_BASE_URL, QWEN_MODEL,
    DATA_DIR
)

# Import caching (optional)
try:
    from backend.modules.cache import get_llm_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    print("[llm_api] Caching module not available, caching disabled")
    get_llm_cache = None  # Placeholder to avoid errors

# Initialize client based on provider
def get_client():
    """Get the appropriate LLM client based on provider configuration"""
    # Note: OpenAI client timeout is handled internally
    # The API server timeout (16-17 seconds) is a server-side limitation we can't control
    timeout = None  # Use default timeout
    
    if LLM_PROVIDER == "deepseek":
        # Support both new (DEEPSEEK_API_KEY) and old (OPENAI_API_KEY) formats
        api_key = DEEPSEEK_API_KEY or OPENAI_API_KEY
        # Base URL logic: prefer DEEPSEEK_BASE_URL, but if using old format (OPENAI_API_KEY), use OPENAI_BASE_URL
        if DEEPSEEK_API_KEY:
            base_url = DEEPSEEK_BASE_URL
        else:
            # Using old format - use OPENAI_BASE_URL if set, otherwise default DeepSeek URL
            base_url = OPENAI_BASE_URL if OPENAI_BASE_URL else DEEPSEEK_BASE_URL
        return OpenAI(api_key=api_key, base_url=base_url)
    elif LLM_PROVIDER == "openai":
        return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    elif LLM_PROVIDER == "qwen":
        api_key = QWEN_API_KEY or OPENAI_API_KEY
        base_url = QWEN_BASE_URL or OPENAI_BASE_URL
        if base_url:
            return OpenAI(api_key=api_key, base_url=base_url)
        else:
            return OpenAI(api_key=api_key)
    elif LLM_PROVIDER == "anthropic":
        try:
            from anthropic import Anthropic
            return Anthropic(api_key=ANTHROPIC_API_KEY)
        except ImportError:
            raise ImportError("Anthropic SDK not installed. Run: pip install anthropic")
    else:
        # Default to DeepSeek
        api_key = DEEPSEEK_API_KEY or OPENAI_API_KEY
        base_url = DEEPSEEK_BASE_URL
        return OpenAI(api_key=api_key, base_url=base_url)

# Lazy client initialization - get fresh client each time to pick up .env changes
def get_fresh_client():
    """Get a fresh client instance (re-initializes to pick up .env changes)"""
    return get_client()

# For backward compatibility, but prefer using get_fresh_client() or get_client()
client = None  # Will be initialized on first use

ANSWER_PROMPT = """You are a code assistant similar to Cursor. Analyze the codebase and answer user questions based on the provided code evidence.

Instructions:
1. Provide a clear, concise answer to the question
2. Reference specific code locations using format: `filename:start-end`
3. Do NOT make up files, functions, or code that doesn't exist
4. If the evidence doesn't fully answer the question, state what's missing
5. For code explanations, explain the logic and flow
6. For refactoring questions, suggest concrete improvements with examples

User question: {question}

Code evidence:
{evidences}
"""

def answer_with_citations(question: str, evidences: List[Dict], model: Optional[str] = None, temperature: float = 0.2, use_cache: bool = True, conversation_history: Optional[List[Dict]] = None):
    """
    Generate answer with code citations using the configured LLM provider.
    
    Args:
        question: User question
        evidences: List of code evidence dicts
        model: Optional model override
        temperature: Sampling temperature
        use_cache: Whether to use response caching (default: True)
        conversation_history: Optional list of previous messages [{"role": "user/assistant", "content": "..."}]
    
    Returns:
        LLM response text
    """
    joined = []
    for ev in evidences:
        file_path = ev.get('file', '')
        start = ev.get('start', 0)
        end = ev.get('end', 0)
        snippet = ev.get('snippet', '')
        joined.append(f"[{file_path}:{start}-{end}]\n```\n{snippet}\n```\n")
    
    content = ANSWER_PROMPT.format(question=question, evidences="\n---\n".join(joined))
    
    # Build messages with conversation history
    messages = []
    
    # Add conversation history if provided
    if conversation_history:
        for msg in conversation_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    
    # Add current question with code context
    messages.append({"role": "user", "content": content})
    
    # Model selection: explicit > LLM_MODEL env > OPENAI_MODEL (backward compat) > default
    if model:
        model_to_use = model
    elif os.getenv("LLM_MODEL"):
        model_to_use = os.getenv("LLM_MODEL")
    elif LLM_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY and os.getenv("OPENAI_MODEL"):
        # Backward compatibility: if using old format with OPENAI_MODEL, use it
        model_to_use = os.getenv("OPENAI_MODEL")
    else:
        model_to_use = LLM_MODEL
    
    # Check privacy mode - skip caching if privacy mode enabled
    try:
        from backend.modules.privacy import is_privacy_mode_enabled
        if is_privacy_mode_enabled():
            use_cache = False
            print(f"[llm_api] Privacy mode enabled - skipping cache")
    except ImportError:
        pass  # Privacy module not available, continue normally
    
    # Check cache first
    if use_cache and CACHE_AVAILABLE:
        try:
            llm_cache = get_llm_cache(cache_dir=f"{DATA_DIR}/cache/llm")
            cached_response = llm_cache.get(content, model_to_use, temperature=temperature)
            if cached_response:
                print(f"[llm_api] Cache HIT for answer_with_citations")
                return cached_response
            print(f"[llm_api] Cache MISS for answer_with_citations")
        except Exception as e:
            print(f"[llm_api] Cache error (continuing without cache): {e}")
    
    # Cache miss or caching disabled - call LLM
    response_text = None
    
    # Use messages list if conversation history provided, otherwise single message
    if not messages:
        messages = [{"role": "user", "content": content}]
    
    # Handle Anthropic separately
    if LLM_PROVIDER == "anthropic":
        try:
            from anthropic import Anthropic
            anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
            message = anthropic_client.messages.create(
                model=model_to_use,
                max_tokens=4096,
                temperature=temperature,
                messages=messages
            )
            response_text = message.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    # OpenAI-compatible providers (DeepSeek, OpenAI, Qwen, etc.)
    if response_text is None:
        # Define LLM call function with retry logic
        def _call_llm():
            try:
                # Get fresh client to pick up any .env changes
                api_client = get_fresh_client()
                rsp = api_client.chat.completions.create(
                    model=model_to_use,
                    messages=messages,
                    temperature=temperature,
                )
                return rsp.choices[0].message.content
            except Exception as e:
                error_msg = str(e).lower()
                # Retry on connection/timeout errors
                if any(keyword in error_msg for keyword in ["timeout", "connection", "network", "temporarily"]):
                    raise RetryableError(f"LLM API transient error ({LLM_PROVIDER}): {str(e)}")
                else:
                    raise Exception(f"LLM API error ({LLM_PROVIDER}): {str(e)}")
        
        # Apply retry logic if available
        if ERROR_HANDLING_AVAILABLE:
            retry_func = retry_with_backoff(
                max_retries=3,
                initial_delay=1.0,
                backoff_factor=2.0,
                retryable_exceptions=(RetryableError,)
            )(_call_llm)
            response_text = retry_func()
        else:
            response_text = _call_llm()
    
    # Cache the response
    if use_cache and CACHE_AVAILABLE and response_text:
        try:
            llm_cache = get_llm_cache(cache_dir=f"{DATA_DIR}/cache/llm")
            llm_cache.set(content, model_to_use, response_text, temperature=temperature)
            print(f"[llm_api] Cached response for answer_with_citations")
        except Exception as e:
            print(f"[llm_api] Error caching response: {e}")
    
    return response_text


def analyze_code(question: str, code_context: List[Dict], analysis_type: str = "explain") -> str:
    """
    Analyze code with different analysis types:
    - explain: Explain what the code does
    - refactor: Suggest refactoring improvements
    - debug: Help debug issues
    - optimize: Suggest performance optimizations
    """
    prompts = {
        "explain": "Explain what this code does, its purpose, and how it works.",
        "refactor": "Suggest how to refactor this code to make it cleaner, more maintainable, and follow best practices.",
        "debug": "Help identify potential bugs, edge cases, or issues in this code.",
        "optimize": "Suggest performance optimizations for this code.",
        "generate": "Generate new code, files, or projects based on the user's requirements. Create complete, working implementations."
    }
    
    full_question = f"{prompts.get(analysis_type, 'Explain')}\n\nQuestion: {question}"
    return answer_with_citations(full_question, code_context, temperature=0.3)


REFACTOR_PROMPT = """You are an expert code refactoring assistant. Analyze the provided code and suggest refactoring improvements with concrete before/after examples.

Instructions:
1. Identify specific issues in the code (readability, maintainability, performance, design patterns, etc.)
2. For EACH suggestion, provide:
   - **Issue**: What problem does this address?
   - **Before**: The original code (exact snippet)
   - **After**: The refactored code (complete, working code)
   - **Benefits**: Why is this better?
3. Prioritize the most impactful refactorings
4. Ensure all code examples are complete and syntactically correct
5. Focus on practical improvements that follow best practices
6. Reference the file and line numbers when relevant

Format your response as markdown with clear sections and code blocks.

Code to refactor:
{code_context}

Specific focus area (if any): {focus}
"""

def suggest_refactoring(code_context: List[Dict], focus: str = "", model: Optional[str] = None, temperature: float = 0.3, use_cache: bool = True) -> Dict:
    """
    Generate refactoring suggestions with before/after examples.
    
    Args:
        code_context: List of code snippets to refactor (from search results)
        focus: Optional focus area (e.g., "performance", "readability", "design patterns")
        model: Optional model override
        temperature: Sampling temperature (0.3 for focused suggestions)
    
    Returns:
        Dict with:
        - suggestions: List of refactoring suggestions
        - summary: Overall assessment
        - code_context: Original code snippets referenced
    """
    # Format code context
    joined = []
    for ev in code_context:
        file_path = ev.get('file', '')
        start = ev.get('start', 0)
        end = ev.get('end', 0)
        snippet = ev.get('snippet', '')
        joined.append(f"File: {file_path} (lines {start}-{end})\n```\n{snippet}\n```\n")
    
    code_text = "\n---\n".join(joined)
    
    # Build prompt
    prompt = REFACTOR_PROMPT.format(
        code_context=code_text,
        focus=focus or "general improvements"
    )
    
    # Model selection
    if model:
        model_to_use = model
    elif os.getenv("LLM_MODEL"):
        model_to_use = os.getenv("LLM_MODEL")
    elif LLM_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY and os.getenv("OPENAI_MODEL"):
        model_to_use = os.getenv("OPENAI_MODEL")
    else:
        model_to_use = LLM_MODEL
    
    # Check cache first
    response_text = None
    if use_cache and CACHE_AVAILABLE:
        try:
            llm_cache = get_llm_cache(cache_dir=f"{DATA_DIR}/cache/llm")
            cached_response = llm_cache.get(prompt, model_to_use, temperature=temperature, max_tokens=4096)
            if cached_response:
                print(f"[llm_api] Cache HIT for suggest_refactoring")
                response_text = cached_response
            else:
                print(f"[llm_api] Cache MISS for suggest_refactoring")
        except Exception as e:
            print(f"[llm_api] Cache error (continuing without cache): {e}")
    
    # Cache miss or caching disabled - call LLM
    if response_text is None:
        # Handle Anthropic separately
        if LLM_PROVIDER == "anthropic":
            try:
                from anthropic import Anthropic
                anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
                message = anthropic_client.messages.create(
                    model=model_to_use,
                    max_tokens=4096,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = message.content[0].text
            except Exception as e:
                raise Exception(f"Anthropic API error: {str(e)}")
        else:
            # OpenAI-compatible providers
            try:
                api_client = get_fresh_client()
                # Increase timeout for refactoring (can take longer for complex code)
                rsp = api_client.chat.completions.create(
                    model=model_to_use,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    timeout=120  # 2 minute timeout for refactoring
                )
                response_text = rsp.choices[0].message.content
            except Exception as e:
                raise Exception(f"LLM API error ({LLM_PROVIDER}): {str(e)}")
        
        # Cache the response
        if use_cache and CACHE_AVAILABLE and response_text:
            try:
                llm_cache = get_llm_cache(cache_dir=f"{DATA_DIR}/cache/llm")
                llm_cache.set(prompt, model_to_use, response_text, temperature=temperature, max_tokens=4096)
                print(f"[llm_api] Cached response for suggest_refactoring")
            except Exception as e:
                print(f"[llm_api] Error caching response: {e}")
    
    # Parse response and structure it
    # For now, return the full response as markdown
    # In the future, we could parse it into structured suggestions
    return {
        "ok": True,
        "refactoring_suggestions": response_text,  # Markdown formatted
        "code_context": code_context,  # Original snippets
        "focus": focus,
        "format": "markdown"  # Could be "structured" in the future
    }


def stream_suggest_refactoring(code_context: List[Dict], focus: str = "", model: Optional[str] = None, temperature: float = 0.3):
    """
    Stream refactoring suggestions for real-time output.
    Yields chunks of refactoring suggestions as they are generated.
    
    Args:
        code_context: List of code snippets to refactor (from search results)
        focus: Optional focus area (e.g., "performance", "readability", "design patterns")
        model: Optional model override
        temperature: Sampling temperature (0.3 for focused suggestions)
    
    Yields:
        String chunks of refactoring suggestions (markdown formatted)
    """
    try:
        # Format code context
        joined = []
        for ev in code_context:
            file_path = ev.get('file', '')
            start = ev.get('start', 0)
            end = ev.get('end', 0)
            snippet = ev.get('snippet', '')
            joined.append(f"File: {file_path} (lines {start}-{end})\n```\n{snippet}\n```\n")
        
        code_text = "\n---\n".join(joined)
        
        # Build prompt
        prompt = REFACTOR_PROMPT.format(
            code_context=code_text,
            focus=focus or "general improvements"
        )
        
        # Model selection
        if model:
            model_to_use = model
        elif os.getenv("LLM_MODEL"):
            model_to_use = os.getenv("LLM_MODEL")
        elif LLM_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY and os.getenv("OPENAI_MODEL"):
            model_to_use = os.getenv("OPENAI_MODEL")
        else:
            model_to_use = LLM_MODEL
        
        print(f"[llm_api] Streaming refactoring suggestions (focus: {focus or 'general'})...")
        
        # Streaming only works with OpenAI-compatible APIs
        if LLM_PROVIDER == "anthropic":
            # Anthropic streaming would need separate implementation
            # For now, fall back to non-streaming
            result = suggest_refactoring(code_context, focus=focus, model=model, temperature=temperature)
            if result.get("ok"):
                suggestions = result.get("refactoring_suggestions", "")
                # Yield in chunks to simulate streaming
                for i in range(0, len(suggestions), 100):
                    yield suggestions[i:i+100]
            else:
                yield f"Error: {result.get('error', 'Unknown error')}"
            return
        
        try:
            # Get fresh client
            api_client = get_fresh_client()
            stream = api_client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=4096,
                stream=True,
                timeout=120
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error: {str(e)}"
    except Exception as e:
        yield f"Error: {str(e)}"


def stream_answer(question: str, evidences: List[Dict], model: Optional[str] = None, conversation_history: Optional[List[Dict]] = None):
    """Stream response for real-time output (like Cursor)"""
    joined = []
    for ev in evidences:
        file_path = ev.get('file', '')
        start = ev.get('start', 0)
        end = ev.get('end', 0)
        snippet = ev.get('snippet', '')
        joined.append(f"[{file_path}:{start}-{end}]\n```\n{snippet}\n```\n")
    
    content = ANSWER_PROMPT.format(question=question, evidences="\n---\n".join(joined))
    
    # Build messages with conversation history
    messages = []
    if conversation_history:
        for msg in conversation_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    messages.append({"role": "user", "content": content})
    
    # Model selection: explicit > LLM_MODEL env > OPENAI_MODEL (backward compat) > default
    if model:
        model_to_use = model
    elif os.getenv("LLM_MODEL"):
        model_to_use = os.getenv("LLM_MODEL")
    elif LLM_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY and os.getenv("OPENAI_MODEL"):
        model_to_use = os.getenv("OPENAI_MODEL")
    else:
        model_to_use = LLM_MODEL
    
    # Streaming only works with OpenAI-compatible APIs
    if LLM_PROVIDER == "anthropic":
        # Anthropic streaming would need separate implementation
        result = answer_with_citations(question, evidences, model_to_use, conversation_history=conversation_history)
        yield result
        return
    
    try:
        # Get fresh client to pick up any .env changes
        api_client = get_fresh_client()
        stream = api_client.chat.completions.create(
            model=model_to_use,
            messages=messages,
            temperature=0.2,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"Error: {str(e)}"

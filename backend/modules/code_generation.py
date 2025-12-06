"""
Code generation module for creating new code from natural language descriptions.
Similar to Cursor's code generation feature - generates new functions, classes, files, etc.
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import re
import ast
import subprocess

from backend.modules.llm_api import get_fresh_client
from backend.modules.search import ripgrep_candidates, fuse_results
from backend.modules.vector_store import FaissStore
from backend.modules.context_retriever import expand_code_context
from backend.modules.multi_repo import repo_id_from_path
from backend.config import LLM_PROVIDER, LLM_MODEL, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, DATA_DIR, TOP_K_EMB, TOP_K_FINAL
import os


GENERATION_PROMPT = """You are an expert code generator. Generate high-quality, production-ready code based on the user's natural language description.

Instructions:
1. Analyze the user's request carefully
2. Understand the codebase context and patterns
3. Generate code that:
   - Matches the existing codebase style and patterns
   - Follows best practices for the target language
   - Is syntactically correct and complete
   - Includes proper error handling
   - Uses appropriate naming conventions
   - Includes necessary imports/dependencies
4. If generating a function, make it complete and functional
5. If generating a class, include all necessary methods
6. If generating a file, include proper structure (imports, exports, etc.)
7. Only return the code - no explanations or markdown unless specifically requested

Target Language: {language}
Generation Type: {generation_type}
Target File: {target_file}

User Request: {request}

Codebase Context (similar code patterns):
{codebase_context}

Generate the code now. Return only the code, properly formatted and complete."""


FUNCTION_GENERATION_PROMPT = """Generate a {language} function based on this description: {request}

Requirements:
- Function should be complete and functional
- Include proper type hints/annotations if applicable
- Include docstring/comments
- Handle edge cases and errors
- Match the codebase style

Codebase Context:
{codebase_context}

Generate only the function code, no explanations."""


CLASS_GENERATION_PROMPT = """Generate a {language} class based on this description: {request}

Requirements:
- Class should be complete with all necessary methods
- Include proper initialization/constructor
- Include docstrings/comments
- Follow object-oriented best practices
- Match the codebase style

Codebase Context:
{codebase_context}

Generate only the class code, no explanations."""


FILE_GENERATION_PROMPT = """Generate a complete {language} file based on this description: {request}

Requirements:
- Include all necessary imports
- Proper file structure
- Complete and functional code
- Follow language-specific conventions
- Match the codebase style

Codebase Context:
{codebase_context}

Generate the complete file content."""


TEST_GENERATION_PROMPT = """Generate {language} unit tests for the following code:

Code to Test:
{code_to_test}

Requirements:
- Use appropriate testing framework ({test_framework})
- Test all functions/methods
- Include edge cases
- Include positive and negative test cases
- Follow testing best practices
- Match the codebase testing style

Codebase Context (existing test patterns):
{codebase_context}

Generate only the test code, no explanations."""


def get_language_from_file(file_path: str) -> str:
    """Determine programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    lang_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.vue': 'vue',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.less': 'less'
    }
    return lang_map.get(ext, 'text')


def get_test_framework(language: str) -> str:
    """Determine testing framework for a language."""
    framework_map = {
        'python': 'pytest',
        'javascript': 'jest',
        'typescript': 'jest',
        'java': 'junit',
        'csharp': 'nunit',
        'go': 'testing',
        'rust': 'cargo test'
    }
    return framework_map.get(language, 'standard')


def get_codebase_context(
    repo_dir: str,
    request: str,
    target_file: Optional[str] = None,
    max_results: int = 5
) -> str:
    """
    Get relevant codebase context for code generation.
    Uses semantic search to find similar code patterns.
    """
    try:
        # Get repo ID and load vector store
        repo_id = repo_id_from_path(repo_dir)
        store = FaissStore(repo_id, base_dir=f"{DATA_DIR}/index")
        
        if not store.index_path.exists():
            return ""
        
        store.load()
        
        # Search for similar code patterns
        vec_results = store.query(request, k=TOP_K_EMB)
        
        # Filter out target file if provided
        if target_file:
            vec_results = [r for r in vec_results if r.get("file") != target_file]
        
        # Limit results
        context_parts = []
        for result in vec_results[:max_results]:
            file_path_rel = result.get("file", "")
            start = result.get("start", 0)
            end = result.get("end", 0)
            snippet = result.get("snippet", "")
            
            # Format as reference
            context_parts.append(f"File: {Path(file_path_rel).name} (lines {start}-{end})\n{snippet}\n")
        
        return "\n---\n".join(context_parts) if context_parts else ""
    
    except Exception as e:
        print(f"[code_generation] Error getting codebase context: {e}")
        return ""


def validate_python_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """Validate Python code syntax."""
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e.msg} at line {e.lineno}"


def validate_javascript_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """Validate JavaScript/TypeScript syntax (basic check)."""
    # Basic validation - check for common syntax errors
    # For production, use a proper JS parser
    try:
        # Check for balanced braces
        if code.count('{') != code.count('}'):
            return False, "Unbalanced braces"
        if code.count('(') != code.count(')'):
            return False, "Unbalanced parentheses"
        if code.count('[') != code.count(']'):
            return False, "Unbalanced brackets"
        return True, None
    except Exception as e:
        return False, f"Validation error: {e}"


def validate_code_syntax(code: str, language: str) -> Tuple[bool, Optional[str]]:
    """Validate code syntax based on language."""
    if language == 'python':
        return validate_python_syntax(code)
    elif language in ['javascript', 'typescript']:
        return validate_javascript_syntax(code)
    else:
        # For other languages, skip validation for now
        return True, None


def generate_code(
    request: str,
    generation_type: str = "function",
    language: Optional[str] = None,
    target_file: Optional[str] = None,
    repo_dir: Optional[str] = None,
    code_to_test: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 2000
) -> Dict:
    """
    Generate code based on natural language description.
    
    Args:
        request: Natural language description of what to generate
        generation_type: Type of generation ("function", "class", "file", "test")
        language: Target programming language (auto-detected from file if not provided)
        target_file: Target file path (for context and language detection)
        repo_dir: Repository directory (for codebase context)
        code_to_test: Code to generate tests for (if generation_type is "test")
        model: Optional model override
        temperature: Temperature for LLM generation
        max_tokens: Maximum tokens for generation
    
    Returns:
        Dict with generated code and metadata
    """
    try:
        # Determine language
        if not language and target_file:
            language = get_language_from_file(target_file)
        elif not language:
            language = "python"  # Default
        
        # Get codebase context
        codebase_context = ""
        if repo_dir:
            codebase_context = get_codebase_context(
                repo_dir,
                request,
                target_file=target_file,
                max_results=5
            )
        
        if not codebase_context:
            codebase_context = "(No codebase context available)"
        
        # Select appropriate prompt based on generation type
        if generation_type == "function":
            prompt = FUNCTION_GENERATION_PROMPT.format(
                language=language,
                request=request,
                codebase_context=codebase_context
            )
        elif generation_type == "class":
            prompt = CLASS_GENERATION_PROMPT.format(
                language=language,
                request=request,
                codebase_context=codebase_context
            )
        elif generation_type == "test":
            if not code_to_test:
                return {
                    "ok": False,
                    "error": "code_to_test is required for test generation"
                }
            test_framework = get_test_framework(language)
            prompt = TEST_GENERATION_PROMPT.format(
                language=language,
                code_to_test=code_to_test,
                test_framework=test_framework,
                codebase_context=codebase_context
            )
        elif generation_type == "file":
            prompt = FILE_GENERATION_PROMPT.format(
                language=language,
                request=request,
                codebase_context=codebase_context
            )
        else:
            # Generic generation
            prompt = GENERATION_PROMPT.format(
                language=language,
                generation_type=generation_type,
                target_file=target_file or "unknown",
                request=request,
                codebase_context=codebase_context
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
        
        # Generate code using LLM
        # Handle Anthropic separately
        if LLM_PROVIDER == "anthropic":
            try:
                from anthropic import Anthropic
                anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
                message = anthropic_client.messages.create(
                    model=model_to_use,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                generated_code = message.content[0].text
            except Exception as e:
                raise Exception(f"Anthropic API error: {str(e)}")
        else:
            # OpenAI-compatible providers
            api_client = get_fresh_client()
            rsp = api_client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=120
            )
            generated_code = rsp.choices[0].message.content
        
        # Clean up generated code (remove markdown code blocks if present)
        generated_code = generated_code.strip()
        
        # Remove markdown code blocks
        if generated_code.startswith("```"):
            lines = generated_code.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            generated_code = "\n".join(lines)
        
        generated_code = generated_code.strip()
        
        # Validate syntax
        syntax_valid = True
        syntax_error = None
        if generation_type != "test":  # Skip validation for tests (they might reference test framework)
            syntax_valid, syntax_error = validate_code_syntax(generated_code, language)
        
        return {
            "ok": True,
            "generated_code": generated_code,
            "language": language,
            "generation_type": generation_type,
            "syntax_valid": syntax_valid,
            "syntax_error": syntax_error,
            "length": len(generated_code),
            "lines": len(generated_code.splitlines())
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"[code_generation] Error generating code: {e}")
        return {
            "ok": False,
            "error": error_msg,
            "generated_code": None
        }


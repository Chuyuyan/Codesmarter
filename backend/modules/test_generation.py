"""
Test generation module for creating unit tests and integration tests.
Generates comprehensive test suites based on existing code patterns and testing frameworks.
"""
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
import re
import json
import os

from backend.modules.llm_api import get_fresh_client
from backend.modules.search import ripgrep_candidates, fuse_results
from backend.modules.vector_store import FaissStore
from backend.modules.multi_repo import repo_id_from_path
from backend.config import (
    LLM_PROVIDER, LLM_MODEL, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY,
    DATA_DIR, TOP_K_EMB, TOP_K_FINAL
)


TEST_GENERATION_PROMPT = """You are an expert test generator. Generate comprehensive unit tests for the provided code.

Instructions:
1. Analyze the code carefully to understand what needs to be tested
2. Identify all functions, methods, classes, and edge cases
3. Generate test cases that cover:
   - Normal/positive cases
   - Edge cases (boundary conditions)
   - Error cases (invalid inputs, exceptions)
   - Edge cases for each parameter
   - Return value validation
   - State changes (for classes/objects)
4. Use the specified testing framework: {test_framework}
5. Follow the existing test patterns in the codebase
6. Include proper setup/teardown if needed
7. Include test fixtures and mocks where appropriate
8. Make tests clear, readable, and well-organized
9. Include descriptive test names that explain what is being tested

Code to Test:
```{language}
{code_to_test}
```

Testing Framework: {test_framework}

Existing Test Patterns in Codebase:
{existing_test_patterns}

Additional Context:
{additional_context}

Generate comprehensive unit tests. Return only the test code, no explanations."""


def detect_test_framework(repo_dir: str, language: str) -> str:
    """
    Detect which testing framework is used in the codebase.
    
    Args:
        repo_dir: Repository directory
        language: Programming language (python, javascript, typescript, etc.)
    
    Returns:
        Framework name (pytest, jest, unittest, mocha, etc.)
    """
    repo_path = Path(repo_dir)
    if not repo_path.exists():
        return "default"
    
    # Check for common test files and configuration
    if language == "python":
        # Check for pytest
        if (repo_path / "pytest.ini").exists() or (repo_path / "setup.cfg").exists():
            try:
                with open(repo_path / "setup.cfg", "r", encoding="utf-8") as f:
                    if "pytest" in f.read():
                        return "pytest"
            except:
                pass
        
        # Check for unittest (default in Python)
        test_files = list(repo_path.rglob("test_*.py")) + list(repo_path.rglob("*_test.py"))
        for test_file in test_files[:3]:  # Check first 3 test files
            try:
                content = test_file.read_text(encoding="utf-8")
                if "import pytest" in content or "from pytest" in content:
                    return "pytest"
                elif "import unittest" in content or "from unittest" in content:
                    return "unittest"
            except:
                continue
        
        return "pytest"  # Default for Python
    
    elif language in ["javascript", "typescript"]:
        # Check for jest
        if (repo_path / "jest.config.js").exists() or (repo_path / "jest.config.ts").exists() or (repo_path / "package.json").exists():
            try:
                package_json = json.loads((repo_path / "package.json").read_text(encoding="utf-8"))
                dev_deps = package_json.get("devDependencies", {})
                if "jest" in dev_deps:
                    return "jest"
                elif "mocha" in dev_deps:
                    return "mocha"
                elif "vitest" in dev_deps:
                    return "vitest"
            except:
                pass
        
        # Check test files
        test_files = list(repo_path.rglob("*.test.js")) + list(repo_path.rglob("*.test.ts")) + list(repo_path.rglob("*.spec.js")) + list(repo_path.rglob("*.spec.ts"))
        for test_file in test_files[:3]:
            try:
                content = test_file.read_text(encoding="utf-8")
                if "jest" in content.lower() or "describe" in content and "test" in content:
                    return "jest"
                elif "mocha" in content.lower():
                    return "mocha"
                elif "vitest" in content.lower():
                    return "vitest"
            except:
                continue
        
        return "jest"  # Default for JS/TS
    
    return "default"


def get_existing_test_patterns(repo_dir: str, language: str) -> str:
    """
    Get existing test patterns from the codebase to match the style.
    
    Args:
        repo_dir: Repository directory
        language: Programming language
    
    Returns:
        String containing example test code patterns
    """
    repo_path = Path(repo_dir)
    if not repo_path.exists():
        return "(No existing test patterns found)"
    
    # Find test files
    test_files = []
    if language == "python":
        test_files = list(repo_path.rglob("test_*.py")) + list(repo_path.rglob("*_test.py"))
    elif language in ["javascript", "typescript"]:
        test_files = list(repo_path.rglob("*.test.js")) + list(repo_path.rglob("*.test.ts")) + list(repo_path.rglob("*.spec.js")) + list(repo_path.rglob("*.spec.ts"))
    
    if not test_files:
        return "(No existing test files found)"
    
    # Get examples from first few test files
    patterns = []
    for test_file in test_files[:3]:  # Get up to 3 examples
        try:
            content = test_file.read_text(encoding="utf-8", errors="ignore")
            # Get first 50 lines as example
            lines = content.splitlines()[:50]
            patterns.append(f"Example from {test_file.name}:\n```\n" + "\n".join(lines) + "\n```\n")
        except:
            continue
    
    if not patterns:
        return "(No existing test patterns found)"
    
    return "\n---\n".join(patterns)


def get_code_to_test(file_path: str, repo_dir: Optional[str] = None, code_snippet: Optional[str] = None) -> Tuple[str, str]:
    """
    Get code to test from file or snippet.
    
    Args:
        file_path: Path to file containing code to test
        repo_dir: Repository directory (if file_path is relative)
        code_snippet: Optional direct code snippet
    
    Returns:
        Tuple of (code_content, language)
    """
    if code_snippet:
        # Use provided snippet
        language = detect_language_from_snippet(code_snippet)
        return code_snippet, language
    
    # Read from file
    file_path_obj = Path(file_path)
    if not file_path_obj.is_absolute() and repo_dir:
        file_path_obj = Path(repo_dir) / file_path
    
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    content = file_path_obj.read_text(encoding="utf-8", errors="ignore")
    language = get_language_from_file(str(file_path_obj))
    
    return content, language


def detect_language_from_snippet(code: str) -> str:
    """Detect programming language from code snippet."""
    # Simple heuristics
    if "def " in code or "import " in code and ("from" in code or "__" in code):
        return "python"
    elif "function " in code or "const " in code or "let " in code or "class " in code and "{" in code:
        return "javascript"
    elif ":" in code and "->" in code or "interface " in code or "type " in code:
        return "typescript"
    return "python"  # Default


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
    }
    return lang_map.get(ext, 'python')


def generate_tests(
    file_path: Optional[str] = None,
    code_snippet: Optional[str] = None,
    repo_dir: Optional[str] = None,
    test_framework: Optional[str] = None,
    test_type: str = "unit",  # "unit" or "integration"
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 3000
) -> Dict:
    """
    Generate tests for code.
    
    Args:
        file_path: Path to file containing code to test
        code_snippet: Optional direct code snippet to test
        repo_dir: Repository directory (for context and framework detection)
        test_framework: Testing framework to use (auto-detected if not provided)
        test_type: Type of tests ("unit" or "integration")
        model: Optional model override
        temperature: Temperature for LLM generation
        max_tokens: Maximum tokens for generation
    
    Returns:
        Dict with generated tests and metadata
    """
    try:
        # Get code to test
        if not code_snippet and not file_path:
            return {
                "ok": False,
                "error": "Either file_path or code_snippet must be provided"
            }
        
        code_to_test, language = get_code_to_test(
            file_path or "test.py",
            repo_dir=repo_dir,
            code_snippet=code_snippet
        )
        
        # Detect test framework if not provided
        if not test_framework and repo_dir:
            test_framework = detect_test_framework(repo_dir, language)
        elif not test_framework:
            # Default frameworks by language
            defaults = {
                "python": "pytest",
                "javascript": "jest",
                "typescript": "jest",
                "java": "junit",
                "csharp": "xunit",
                "go": "testing"
            }
            test_framework = defaults.get(language, "default")
        
        # Get existing test patterns
        existing_test_patterns = ""
        if repo_dir:
            existing_test_patterns = get_existing_test_patterns(repo_dir, language)
        else:
            existing_test_patterns = "(No existing test patterns found)"
        
        # Get codebase context for additional context
        additional_context = ""
        if repo_dir:
            try:
                repo_id = repo_id_from_path(repo_dir)
                store = FaissStore(repo_id, base_dir=f"{DATA_DIR}/index")
                
                if store.index_path.exists():
                    store.load()
                    vec_results = store.query(f"test {code_to_test[:100]}", k=min(TOP_K_EMB, 3))
                    
                    context_parts = []
                    for result in vec_results:
                        rel_file = result.get("file", "")
                        snippet = result.get("snippet", "")
                        if "test" in rel_file.lower():
                            context_parts.append(f"File: {Path(rel_file).name}\n{snippet[:300]}\n")
                    
                    if context_parts:
                        additional_context = "\n---\n".join(context_parts)
            except Exception as e:
                print(f"[test_generation] Error getting codebase context: {e}")
        
        if not additional_context:
            additional_context = "(No additional context available)"
        
        # Build prompt
        prompt = TEST_GENERATION_PROMPT.format(
            language=language,
            code_to_test=code_to_test[:3000],  # Limit code size
            test_framework=test_framework,
            existing_test_patterns=existing_test_patterns[:2000],  # Limit pattern size
            additional_context=additional_context[:1000]  # Limit context size
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
        
        print(f"[test_generation] Generating {test_type} tests for {Path(file_path).name if file_path else 'code snippet'} using {test_framework}")
        print(f"[test_generation] Prompt length: {len(prompt)} chars")
        print(f"[test_generation] Using model: {model_to_use}")
        print(f"[test_generation] Max tokens: {max_tokens}")
        
        # Generate tests using LLM
        # Handle Anthropic separately
        if LLM_PROVIDER == "anthropic":
            try:
                print(f"[test_generation] Calling Anthropic API...")
                from anthropic import Anthropic
                anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
                message = anthropic_client.messages.create(
                    model=model_to_use,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                test_code = message.content[0].text
                print(f"[test_generation] Anthropic API call completed, response length: {len(test_code)} chars")
            except Exception as e:
                print(f"[test_generation] Anthropic API error: {e}")
                import traceback
                traceback.print_exc()
                raise Exception(f"Anthropic API error: {str(e)}")
        else:
            # OpenAI-compatible providers
            print(f"[test_generation] Calling OpenAI-compatible API ({LLM_PROVIDER})...")
            api_client = get_fresh_client()
            try:
                rsp = api_client.chat.completions.create(
                    model=model_to_use,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=180
                )
                test_code = rsp.choices[0].message.content
                print(f"[test_generation] LLM API call completed, response length: {len(test_code)} chars")
            except Exception as e:
                print(f"[test_generation] LLM API error: {e}")
                import traceback
                traceback.print_exc()
                raise Exception(f"LLM API error: {str(e)}")
        
        # Clean up the response (remove markdown code blocks if present)
        test_code = test_code.strip()
        
        # Remove markdown code blocks if present
        if "```" in test_code:
            # Extract code from markdown code block
            code_block_match = re.search(r'```(?:python|javascript|typescript|js|ts)?\s*\n(.*?)\n```', test_code, re.DOTALL)
            if code_block_match:
                test_code = code_block_match.group(1)
            else:
                # Try simpler pattern
                lines = test_code.splitlines()
                # Remove first line if it starts with ```
                if lines and lines[0].startswith('```'):
                    lines = lines[1:]
                # Remove last line if it's ```
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                test_code = '\n'.join(lines)
        
        # Determine test file name
        test_file_name = None
        if file_path:
            file_name = Path(file_path).stem
            if language == "python":
                test_file_name = f"test_{file_name}.py"
            elif language in ["javascript", "typescript"]:
                ext = Path(file_path).suffix
                test_file_name = f"{file_name}.test{ext}"
        
        return {
            "ok": True,
            "test_code": test_code,
            "test_framework": test_framework,
            "language": language,
            "test_type": test_type,
            "test_file_name": test_file_name,
            "file_path": file_path,
            "code_to_test": code_to_test[:500] if len(code_to_test) > 500 else code_to_test,  # Preview
            "lines": len(test_code.splitlines())
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"[test_generation] Error in generate_tests: {e}")
        import traceback
        traceback.print_exc()
        return {
            "ok": False,
            "error": error_msg,
            "test_code": None
        }


def stream_generate_tests(
    file_path: Optional[str] = None,
    code_snippet: Optional[str] = None,
    repo_dir: Optional[str] = None,
    test_framework: Optional[str] = None,
    test_type: str = "unit",
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 3000
):
    """
    Stream test generation for real-time output.
    Yields chunks of test code as they are generated.
    
    Args:
        Same as generate_tests
    
    Yields:
        String chunks of test code
    """
    try:
        # Get code to test
        if not code_snippet and not file_path:
            yield f"Error: Either file_path or code_snippet must be provided"
            return
        
        code_to_test, language = get_code_to_test(
            file_path or "test.py",
            repo_dir=repo_dir,
            code_snippet=code_snippet
        )
        
        # Detect test framework if not provided
        if not test_framework and repo_dir:
            test_framework = detect_test_framework(repo_dir, language)
        elif not test_framework:
            defaults = {
                "python": "pytest",
                "javascript": "jest",
                "typescript": "jest",
                "java": "junit",
                "csharp": "xunit",
                "go": "testing"
            }
            test_framework = defaults.get(language, "default")
        
        # Get existing test patterns
        existing_test_patterns = ""
        if repo_dir:
            existing_test_patterns = get_existing_test_patterns(repo_dir, language)
        else:
            existing_test_patterns = "(No existing test patterns found)"
        
        # Get codebase context
        additional_context = ""
        if repo_dir:
            try:
                repo_id = repo_id_from_path(repo_dir)
                store = FaissStore(repo_id, base_dir=f"{DATA_DIR}/index")
                
                if store.index_path.exists():
                    store.load()
                    vec_results = store.query(f"test {code_to_test[:100]}", k=min(TOP_K_EMB, 3))
                    
                    context_parts = []
                    for result in vec_results:
                        rel_file = result.get("file", "")
                        snippet = result.get("snippet", "")
                        if "test" in rel_file.lower():
                            context_parts.append(f"File: {Path(rel_file).name}\n{snippet[:300]}\n")
                    
                    if context_parts:
                        additional_context = "\n---\n".join(context_parts)
            except Exception as e:
                print(f"[test_generation] Error getting codebase context: {e}")
        
        if not additional_context:
            additional_context = "(No additional context available)"
        
        # Build prompt
        prompt = TEST_GENERATION_PROMPT.format(
            language=language,
            code_to_test=code_to_test[:3000],
            test_framework=test_framework,
            existing_test_patterns=existing_test_patterns[:2000],
            additional_context=additional_context[:1000]
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
        
        print(f"[test_generation] Streaming {test_type} tests for {Path(file_path).name if file_path else 'code snippet'} using {test_framework}")
        
        # Streaming only works with OpenAI-compatible APIs
        if LLM_PROVIDER == "anthropic":
            # Anthropic streaming would need separate implementation
            # For now, fall back to non-streaming
            result = generate_tests(
                file_path=file_path,
                code_snippet=code_snippet,
                repo_dir=repo_dir,
                test_framework=test_framework,
                test_type=test_type,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            if result.get("ok"):
                test_code = result.get("test_code", "")
                # Yield in chunks to simulate streaming
                for i in range(0, len(test_code), 100):
                    yield test_code[i:i+100]
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
                max_tokens=max_tokens,
                stream=True,
                timeout=180
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error: {str(e)}"
    except Exception as e:
        yield f"Error: {str(e)}"


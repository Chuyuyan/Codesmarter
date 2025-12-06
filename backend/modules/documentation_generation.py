"""
Documentation generation module for creating docstrings, README files, and API documentation.
Generates comprehensive documentation based on code analysis.
"""
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
import re
import json
import os
import ast

from backend.modules.llm_api import get_fresh_client
from backend.modules.search import ripgrep_candidates, fuse_results
from backend.modules.vector_store import FaissStore
from backend.modules.multi_repo import repo_id_from_path
from backend.config import (
    LLM_PROVIDER, LLM_MODEL, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY,
    DATA_DIR, TOP_K_EMB, TOP_K_FINAL
)


DOCSTRING_GENERATION_PROMPT = """You are an expert documentation generator. Generate comprehensive docstrings for the provided code.

Instructions:
1. Analyze the code carefully to understand:
   - Function/class purpose
   - Parameters and their types
   - Return values and types
   - Exceptions that may be raised
   - Side effects or state changes
   - Usage examples
2. Generate docstrings following the specified format: {doc_format}
3. Include:
   - Clear description of what the code does
   - Parameter descriptions with types
   - Return value descriptions with types
   - Exception descriptions (if any)
   - Usage examples (if helpful)
4. Follow the existing documentation style in the codebase

Code to Document:
```{language}
{code_to_document}
```

Documentation Format: {doc_format}
Target: {target_type} ({target_name})

Existing Documentation Patterns in Codebase:
{existing_doc_patterns}

Additional Context:
{additional_context}

Generate the documentation. Return only the docstring/documentation, no explanations."""


README_GENERATION_PROMPT = """You are an expert README generator. Generate a comprehensive README.md file for this project.

Instructions:
1. Analyze the codebase structure and identify:
   - Project name and description
   - Main features and functionality
   - Installation requirements and setup steps
   - Usage examples
   - API endpoints (if applicable)
   - Configuration options
   - Dependencies
   - Contributing guidelines (optional)
   - License information (if available)
2. Generate a well-structured README.md with:
   - Project title and description
   - Features list
   - Installation instructions
   - Usage examples with code snippets
   - API documentation (if applicable)
   - Configuration guide
   - Dependencies list
   - Contributing section (optional)
   - License section (if available)
3. Use proper Markdown formatting
4. Include code examples where helpful
5. Make it clear and professional

Project Structure Analysis:
{project_structure}

Main Files and Code:
{main_code}

Existing Documentation (if any):
{existing_docs}

Generate a comprehensive README.md file. Return only the Markdown content."""


API_DOC_GENERATION_PROMPT = """You are an expert API documentation generator. Generate comprehensive API documentation for the provided code.

Instructions:
1. Analyze the code to identify:
   - All API endpoints (if applicable)
   - Functions and methods that form the API
   - Request/response formats
   - Parameters and return types
   - Error codes and exceptions
   - Authentication requirements (if any)
2. Generate API documentation in {format} format
3. Include:
   - Endpoint/method descriptions
   - Request parameters (query, body, headers)
   - Response formats
   - Status codes
   - Error responses
   - Code examples
4. Follow REST API documentation conventions

Code to Document:
```{language}
{code_to_document}
```

Documentation Format: {format}

Existing API Documentation Patterns:
{existing_patterns}

Additional Context:
{additional_context}

Generate comprehensive API documentation. Return only the documentation content."""


def detect_doc_format(language: str, code: str = "") -> str:
    """
    Detect documentation format based on language and code style.
    
    Args:
        language: Programming language
        code: Optional code snippet to analyze
    
    Returns:
        Documentation format (google, numpy, restructuredtext, jsdoc, etc.)
    """
    if language == "python":
        # Check for existing docstring style in code
        if code:
            if '"""' in code and ":param" in code or ":type" in code:
                return "google"  # Google-style docstrings
            elif '"""' in code and ":param" in code and "Args:" in code:
                return "numpy"  # NumPy-style docstrings
            elif '"""' in code or "'''" in code:
                return "google"  # Default to Google-style for Python
        
        # Check for common patterns
        if ":param" in code or ":return:" in code:
            return "google"
        elif "Args:" in code and "Returns:" in code:
            return "google"
        
        return "google"  # Default for Python
    
    elif language in ["javascript", "typescript"]:
        # Check for JSDoc style
        if "/**" in code or "* @param" in code or "* @returns" in code:
            return "jsdoc"
        return "jsdoc"  # Default for JS/TS
    
    return "default"


def get_existing_doc_patterns(repo_dir: str, language: str, doc_type: str = "docstring") -> str:
    """
    Get existing documentation patterns from the codebase.
    
    Args:
        repo_dir: Repository directory
        language: Programming language
        doc_type: Type of documentation ("docstring", "readme", "api")
    
    Returns:
        String containing example documentation patterns
    """
    repo_path = Path(repo_dir)
    if not repo_path.exists():
        return "(No existing documentation patterns found)"
    
    patterns = []
    
    if doc_type == "docstring":
        # Find files with docstrings
        if language == "python":
            py_files = list(repo_path.rglob("*.py"))
            for py_file in py_files[:5]:  # Check first 5 Python files
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    # Find docstrings
                    docstring_match = re.search(r'(""".*?""")|(\'\'\'.*?\'\'\')', content, re.DOTALL)
                    if docstring_match:
                        docstring = docstring_match.group(0)
                        patterns.append(f"Example from {py_file.name}:\n```python\n{docstring[:300]}\n```\n")
                except:
                    continue
        
        elif language in ["javascript", "typescript"]:
            # Limit search to avoid deep recursion in large repos
            js_files = list(repo_path.glob("*.js")) + list(repo_path.glob("*.ts"))  # Top-level first
            if len(js_files) < 5:
                # Add some from subdirectories (but limit depth and skip node_modules)
                js_files.extend([f for f in repo_path.rglob("*.js") if 'node_modules' not in str(f)][:5-len(js_files)])
                js_files.extend([f for f in repo_path.rglob("*.ts") if 'node_modules' not in str(f)][:5-len(js_files)])
            for js_file in js_files[:5]:
                try:
                    content = js_file.read_text(encoding="utf-8", errors="ignore")
                    # Find JSDoc comments
                    jsdoc_match = re.search(r'/\*\*.*?\*/', content, re.DOTALL)
                    if jsdoc_match:
                        jsdoc = jsdoc_match.group(0)
                        patterns.append(f"Example from {js_file.name}:\n```javascript\n{jsdoc[:300]}\n```\n")
                except:
                    continue
    
    elif doc_type == "readme":
        # Check for existing README files
        readme_files = list(repo_path.glob("README*"))
        for readme_file in readme_files[:2]:
            try:
                content = readme_file.read_text(encoding="utf-8", errors="ignore")
                patterns.append(f"Example from {readme_file.name}:\n```markdown\n{content[:500]}\n```\n")
            except:
                continue
    
    if not patterns:
        return "(No existing documentation patterns found)"
    
    return "\n---\n".join(patterns)


def get_project_structure(repo_dir: str, max_depth: int = 2) -> str:
    """
    Analyze project structure for README generation (optimized for large repositories).
    
    Args:
        repo_dir: Repository directory
        max_depth: Maximum directory depth to analyze (default: 2)
    
    Returns:
        String describing project structure
    """
    repo_path = Path(repo_dir)
    if not repo_path.exists():
        return "(Project structure not available)"
    
    structure_parts = []
    
    try:
        # Get top-level files (limit to important ones)
        top_level = []
        important_files = ["main.py", "app.py", "index.py", "index.js", "index.ts", "server.py", 
                          "requirements.txt", "package.json", "setup.py", "pyproject.toml",
                          "README.md", "README.rst", "Dockerfile", "docker-compose.yml",
                          "Makefile", "CMakeLists.txt", ".env.example"]
        
        for item in repo_path.iterdir():
            if item.is_file() and item.name in important_files:
                top_level.append(item.name)
            elif item.is_file() and len(top_level) < 15:  # Limit total files
                top_level.append(item.name)
        
        if top_level:
            structure_parts.append(f"Top-level files: {', '.join(top_level[:15])}")
        
        # Get top-level directories (limit depth to avoid deep recursion)
        directories = []
        ignored_dirs = {'.git', '.venv', 'venv', '__pycache__', 'node_modules', '.next', 
                       'dist', 'build', '.pytest_cache', '.mypy_cache', '.idea', '.vscode'}
        
        for item in repo_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in ignored_dirs:
                directories.append(item.name)
                if len(directories) >= 15:  # Limit directories
                    break
        
        if directories:
            structure_parts.append(f"Top-level directories: {', '.join(directories)}")
        
        # Check for common files (quick checks)
        if (repo_path / "requirements.txt").exists():
            try:
                req_content = (repo_path / "requirements.txt").read_text(encoding="utf-8", errors="ignore")[:500]
                req_lines = [line.strip() for line in req_content.splitlines() if line.strip() and not line.startswith('#')][:10]
                structure_parts.append(f"Python dependencies (sample): {', '.join(req_lines[:5])}")
            except:
                structure_parts.append("Has requirements.txt (Python project)")
        
        if (repo_path / "package.json").exists():
            try:
                package_json = json.loads((repo_path / "package.json").read_text(encoding="utf-8", errors="ignore"))
                name = package_json.get("name", "unknown")
                version = package_json.get("version", "unknown")
                structure_parts.append(f"Node.js project: {name} v{version}")
                
                # Get some dependencies
                deps = list(package_json.get("dependencies", {}).keys())[:5]
                if deps:
                    structure_parts.append(f"Key dependencies: {', '.join(deps)}")
            except:
                structure_parts.append("Has package.json (Node.js project)")
        
        if (repo_path / "setup.py").exists() or (repo_path / "pyproject.toml").exists():
            structure_parts.append("Has Python package configuration")
        
        # Check for entry point files
        entry_points = []
        for entry in ["main.py", "app.py", "index.py", "index.js", "index.ts", "server.py", "__main__.py"]:
            if (repo_path / entry).exists():
                entry_points.append(entry)
        
        if entry_points:
            structure_parts.append(f"Entry points: {', '.join(entry_points)}")
    
    except Exception as e:
        print(f"[documentation_generation] Error analyzing project structure: {e}")
        structure_parts.append("(Project structure analysis encountered errors)")
    
    return "\n".join(structure_parts) if structure_parts else "(Project structure not available)"


def get_main_code(repo_dir: str, max_files: int = 3, max_lines_per_file: int = 40, max_total_size: int = 5000) -> str:
    """
    Get main code files for README generation (optimized for large repositories).
    
    Args:
        repo_dir: Repository directory
        max_files: Maximum number of files to include (default: 3)
        max_lines_per_file: Maximum lines per file (default: 40)
        max_total_size: Maximum total content size in characters (default: 5000)
    
    Returns:
        String with main code snippets
    """
    repo_path = Path(repo_dir)
    if not repo_path.exists():
        return "(Main code not available)"
    
    code_parts = []
    total_size = 0
    ignored_dirs = {'.git', '.venv', 'venv', '__pycache__', 'node_modules', '.next', 
                   'dist', 'build', '.pytest_cache', '.mypy_cache', '.idea', '.vscode',
                   'tests', 'test', '__tests__', 'spec'}
    
    try:
        # Find main entry points (priority files)
        entry_points = []
        priority_files = ["main.py", "app.py", "index.py", "index.js", "index.ts", 
                         "server.py", "__main__.py", "run.py", "start.py"]
        
        for priority_file in priority_files:
            file_path = repo_path / priority_file
            if file_path.exists() and len(entry_points) < max_files:
                entry_points.append(file_path)
        
        # If not enough entry points, find top-level source files (not in ignored dirs)
        if len(entry_points) < max_files:
            # Get Python files from root or main directories only
            for item in repo_path.iterdir():
                if len(entry_points) >= max_files:
                    break
                
                if item.is_file() and item.suffix in ['.py', '.js', '.ts', '.jsx', '.tsx']:
                    if not any(ignored in str(item) for ignored in ignored_dirs):
                        entry_points.append(item)
        
        # Process files with size limits
        for file_path in entry_points[:max_files]:
            if total_size >= max_total_size:
                break
                
            try:
                # Check file size first (skip very large files)
                file_size = file_path.stat().st_size
                if file_size > 100000:  # Skip files larger than 100KB
                    continue
                
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                
                # Get first N lines as preview
                lines = content.splitlines()[:max_lines_per_file]
                preview = "\n".join(lines)
                
                # Truncate if still too large
                if len(preview) > 1500:
                    preview = preview[:1500] + "\n... (truncated)"
                
                code_snippet = f"File: {file_path.name}\n```{get_language_from_file(str(file_path))}\n{preview}\n```\n"
                
                if total_size + len(code_snippet) <= max_total_size:
                    code_parts.append(code_snippet)
                    total_size += len(code_snippet)
                else:
                    # Add truncated version if space allows
                    remaining_space = max_total_size - total_size
                    if remaining_space > 500:
                        truncated = code_snippet[:remaining_space] + "\n... (truncated)"
                        code_parts.append(truncated)
                    break
                    
            except Exception as e:
                print(f"[documentation_generation] Error reading {file_path}: {e}")
                continue
        
        if not code_parts:
            return "(Main code not available - files may be too large or not found)"
        
        return "\n---\n".join(code_parts)
    
    except Exception as e:
        print(f"[documentation_generation] Error in get_main_code: {e}")
        return "(Main code not available - error during analysis)"


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


def generate_documentation(
    doc_type: str,  # "docstring", "readme", "api"
    file_path: Optional[str] = None,
    code_snippet: Optional[str] = None,
    repo_dir: Optional[str] = None,
    doc_format: Optional[str] = None,
    target_name: Optional[str] = None,  # Function/class name for docstrings
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 3000
) -> Dict:
    """
    Generate documentation for code.
    
    Args:
        doc_type: Type of documentation ("docstring", "readme", "api")
        file_path: Path to file containing code (optional)
        code_snippet: Direct code snippet (optional)
        repo_dir: Repository directory (for context)
        doc_format: Documentation format (auto-detected if not provided)
        target_name: Name of function/class for docstrings
        model: Optional model override
        temperature: Temperature for LLM generation
        max_tokens: Maximum tokens for generation
    
    Returns:
        Dict with generated documentation and metadata
    """
    try:
        if doc_type == "readme":
            # README generation - analyze whole project
            if not repo_dir:
                return {
                    "ok": False,
                    "error": "repo_dir is required for README generation"
                }
            
            project_structure = get_project_structure(repo_dir)
            main_code = get_main_code(repo_dir)
            existing_docs = get_existing_doc_patterns(repo_dir, "python", "readme")
            
            # Build prompt
            prompt = README_GENERATION_PROMPT.format(
                project_structure=project_structure[:2000],
                main_code=main_code[:3000],
                existing_docs=existing_docs[:1000]
            )
            
            language = "markdown"
            target_name = "README.md"
        
        else:
            # Docstring or API documentation - analyze specific code
            if not code_snippet and not file_path:
                return {
                    "ok": False,
                    "error": "Either file_path or code_snippet is required for docstring/api documentation"
                }
            
            # Get code to document
            if code_snippet:
                code_to_document = code_snippet
                language = detect_language_from_snippet(code_snippet)
            else:
                file_path_obj = Path(file_path)
                if not file_path_obj.is_absolute() and repo_dir:
                    file_path_obj = Path(repo_dir) / file_path
                
                if not file_path_obj.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                code_to_document = file_path_obj.read_text(encoding="utf-8", errors="ignore")
                language = get_language_from_file(str(file_path_obj))
            
            # Detect doc format if not provided
            if not doc_format:
                doc_format = detect_doc_format(language, code_to_document)
            
            # Get existing patterns
            existing_patterns = ""
            if repo_dir:
                existing_patterns = get_existing_doc_patterns(repo_dir, language, doc_type)
            else:
                existing_patterns = "(No existing documentation patterns found)"
            
            # Get codebase context
            additional_context = ""
            if repo_dir:
                try:
                    repo_id = repo_id_from_path(repo_dir)
                    store = FaissStore(repo_id, base_dir=f"{DATA_DIR}/index")
                    
                    if store.index_path.exists():
                        store.load()
                        vec_results = store.query(f"documentation {code_to_document[:100]}", k=min(TOP_K_EMB, 3))
                        
                        context_parts = []
                        for result in vec_results:
                            rel_file = result.get("file", "")
                            snippet = result.get("snippet", "")
                            if "doc" in rel_file.lower() or "readme" in rel_file.lower():
                                context_parts.append(f"File: {Path(rel_file).name}\n{snippet[:300]}\n")
                        
                        if context_parts:
                            additional_context = "\n---\n".join(context_parts)
                except Exception as e:
                    print(f"[documentation_generation] Error getting codebase context: {e}")
            
            if not additional_context:
                additional_context = "(No additional context available)"
            
            # Build prompt based on doc type
            if doc_type == "docstring":
                prompt = DOCSTRING_GENERATION_PROMPT.format(
                    language=language,
                    code_to_document=code_to_document[:3000],
                    doc_format=doc_format,
                    target_type="function" if "def " in code_to_document else "class",
                    target_name=target_name or "target",
                    existing_doc_patterns=existing_patterns[:2000],
                    additional_context=additional_context[:1000]
                )
            elif doc_type == "api":
                prompt = API_DOC_GENERATION_PROMPT.format(
                    language=language,
                    code_to_document=code_to_document[:3000],
                    format=doc_format or "markdown",
                    existing_patterns=existing_patterns[:2000],
                    additional_context=additional_context[:1000]
                )
            else:
                return {
                    "ok": False,
                    "error": f"Unknown documentation type: {doc_type}"
                }
        
        # Model selection
        if model:
            model_to_use = model
        elif os.getenv("LLM_MODEL"):
            model_to_use = os.getenv("LLM_MODEL")
        elif LLM_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY and os.getenv("OPENAI_MODEL"):
            model_to_use = os.getenv("OPENAI_MODEL")
        else:
            model_to_use = LLM_MODEL
        
        print(f"[documentation_generation] Generating {doc_type} documentation ({doc_format or 'default'} format)...")
        
        # Generate documentation using LLM
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
                documentation = message.content[0].text
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
                timeout=180
            )
            documentation = rsp.choices[0].message.content
        
        # Clean up the response
        documentation = documentation.strip()
        
        # Remove markdown code blocks if present (for docstrings)
        if doc_type == "docstring" and "```" in documentation:
            code_block_match = re.search(r'```(?:python|javascript|typescript)?\s*\n(.*?)\n```', documentation, re.DOTALL)
            if code_block_match:
                documentation = code_block_match.group(1)
            else:
                # Try simpler pattern
                lines = documentation.splitlines()
                if lines and lines[0].startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                documentation = '\n'.join(lines)
        
        return {
            "ok": True,
            "documentation": documentation,
            "doc_type": doc_type,
            "doc_format": doc_format or "default",
            "language": language,
            "target_name": target_name,
            "file_path": file_path,
            "lines": len(documentation.splitlines())
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"[documentation_generation] Error in generate_documentation: {e}")
        import traceback
        traceback.print_exc()
        return {
            "ok": False,
            "error": error_msg,
            "documentation": None
        }


def stream_generate_documentation(
    doc_type: str,  # "docstring", "readme", "api"
    file_path: Optional[str] = None,
    code_snippet: Optional[str] = None,
    repo_dir: Optional[str] = None,
    doc_format: Optional[str] = None,
    target_name: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 3000
):
    """
    Stream documentation generation for real-time output.
    Yields chunks of documentation as they are generated.
    
    Args:
        Same as generate_documentation
    
    Yields:
        String chunks of documentation
    """
    try:
        # Validate doc type
        if doc_type not in ["docstring", "readme", "api"]:
            yield f"Error: Invalid doc_type: {doc_type}. Must be 'docstring', 'readme', or 'api'"
            return
        
        if doc_type == "readme":
            # README generation - analyze whole project
            if not repo_dir:
                yield f"Error: repo_dir is required for README generation"
                return
            
            project_structure = get_project_structure(repo_dir)
            main_code = get_main_code(repo_dir)
            existing_docs = get_existing_doc_patterns(repo_dir, "python", "readme")
            
            # Build prompt
            prompt = README_GENERATION_PROMPT.format(
                project_structure=project_structure[:2000],
                main_code=main_code[:3000],
                existing_docs=existing_docs[:1000]
            )
        
        else:
            # Docstring or API documentation - analyze specific code
            if not code_snippet and not file_path:
                yield f"Error: Either file_path or code_snippet is required for docstring/api documentation"
                return
            
            # Get code to document
            if code_snippet:
                code_to_document = code_snippet
                language = detect_language_from_snippet(code_snippet)
            else:
                file_path_obj = Path(file_path)
                if not file_path_obj.is_absolute() and repo_dir:
                    file_path_obj = Path(repo_dir) / file_path
                
                if not file_path_obj.exists():
                    yield f"Error: File not found: {file_path}"
                    return
                
                code_to_document = file_path_obj.read_text(encoding="utf-8", errors="ignore")
                language = get_language_from_file(str(file_path_obj))
            
            # Detect doc format if not provided
            if not doc_format:
                doc_format = detect_doc_format(language, code_to_document)
            
            # Get existing patterns
            existing_patterns = ""
            if repo_dir:
                existing_patterns = get_existing_doc_patterns(repo_dir, language, doc_type)
            else:
                existing_patterns = "(No existing documentation patterns found)"
            
            # Get codebase context
            additional_context = ""
            if repo_dir:
                try:
                    repo_id = repo_id_from_path(repo_dir)
                    store = FaissStore(repo_id, base_dir=f"{DATA_DIR}/index")
                    
                    if store.index_path.exists():
                        store.load()
                        vec_results = store.query(f"documentation {code_to_document[:100]}", k=min(TOP_K_EMB, 3))
                        
                        context_parts = []
                        for result in vec_results:
                            rel_file = result.get("file", "")
                            snippet = result.get("snippet", "")
                            if "doc" in rel_file.lower() or "readme" in rel_file.lower():
                                context_parts.append(f"File: {Path(rel_file).name}\n{snippet[:300]}\n")
                        
                        if context_parts:
                            additional_context = "\n---\n".join(context_parts)
                except Exception as e:
                    print(f"[documentation_generation] Error getting codebase context: {e}")
            
            if not additional_context:
                additional_context = "(No additional context available)"
            
            # Build prompt based on doc type
            if doc_type == "docstring":
                prompt = DOCSTRING_GENERATION_PROMPT.format(
                    language=language,
                    code_to_document=code_to_document[:3000],
                    doc_format=doc_format,
                    target_type="function" if "def " in code_to_document else "class",
                    target_name=target_name or "target",
                    existing_doc_patterns=existing_patterns[:2000],
                    additional_context=additional_context[:1000]
                )
            elif doc_type == "api":
                prompt = API_DOC_GENERATION_PROMPT.format(
                    language=language,
                    code_to_document=code_to_document[:3000],
                    format=doc_format or "markdown",
                    existing_patterns=existing_patterns[:2000],
                    additional_context=additional_context[:1000]
                )
            else:
                yield f"Error: Unknown documentation type: {doc_type}"
                return
        
        # Model selection
        if model:
            model_to_use = model
        elif os.getenv("LLM_MODEL"):
            model_to_use = os.getenv("LLM_MODEL")
        elif LLM_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY and os.getenv("OPENAI_MODEL"):
            model_to_use = os.getenv("OPENAI_MODEL")
        else:
            model_to_use = LLM_MODEL
        
        print(f"[documentation_generation] Streaming {doc_type} documentation ({doc_format or 'default'} format)...")
        
        # Streaming only works with OpenAI-compatible APIs
        if LLM_PROVIDER == "anthropic":
            # Anthropic streaming would need separate implementation
            # For now, fall back to non-streaming
            result = generate_documentation(
                doc_type=doc_type,
                file_path=file_path,
                code_snippet=code_snippet,
                repo_dir=repo_dir,
                doc_format=doc_format,
                target_name=target_name,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            if result.get("ok"):
                documentation = result.get("documentation", "")
                # Yield in chunks to simulate streaming
                for i in range(0, len(documentation), 100):
                    yield documentation[i:i+100]
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


def detect_language_from_snippet(code: str) -> str:
    """Detect programming language from code snippet."""
    if "def " in code or "import " in code and ("from" in code or "__" in code):
        return "python"
    elif "function " in code or "const " in code or "let " in code or ("class " in code and "{" in code):
        return "javascript"
    elif ":" in code and "->" in code or "interface " in code or "type " in code:
        return "typescript"
    return "python"  # Default


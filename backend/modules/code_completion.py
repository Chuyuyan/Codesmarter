"""
Code completion module for inline autocomplete suggestions.
Similar to Cursor's Tab feature - generates code completions based on context.
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import re

from backend.modules.llm_api import get_fresh_client
from backend.modules.search import ripgrep_candidates, fuse_results
from backend.modules.vector_store import FaissStore
from backend.modules.context_retriever import expand_code_context
from backend.modules.multi_repo import repo_id_from_path
from backend.config import LLM_PROVIDER, LLM_MODEL, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, DATA_DIR, TOP_K_EMB, TOP_K_FINAL
import os


COMPLETION_PROMPT = """You are an expert code assistant providing inline code completions. Based on the current code context, generate a natural continuation of the code.

Instructions:
1. Analyze the current code context (file content, cursor position, surrounding code)
2. Understand the coding pattern and style
3. Generate a continuation that:
   - Matches the existing code style
   - Completes the current thought/logic
   - Uses appropriate patterns and conventions
   - Is syntactically correct
4. Only generate code - no explanations or markdown
5. If the current line is incomplete, complete it
6. If the current line is complete, suggest the next logical code block
7. Respect indentation and formatting
8. Keep completions concise (prefer shorter, focused completions)

Current File: {file_path}
Language: {language}
Cursor Position: Line {line}, Column {column}

Current File Content (around cursor):
```{language}
{before_cursor}{cursor_marker}{after_cursor}
```

Related Code from Codebase:
{related_code}

Generate a code completion starting from the cursor position. Only return the completion code, nothing else."""


def extract_code_context(
    file_content: str,
    cursor_line: int,
    cursor_column: int,
    context_lines_before: int = 50,
    context_lines_after: int = 20
) -> Tuple[str, str, str]:
    """
    Extract code context around cursor position.
    
    Args:
        file_content: Full file content
        cursor_line: Cursor line number (1-indexed)
        cursor_column: Cursor column number (1-indexed)
        context_lines_before: Lines before cursor to include
        context_lines_after: Lines after cursor to include
    
    Returns:
        Tuple of (before_cursor, cursor_marker, after_cursor)
    """
    lines = file_content.splitlines()
    total_lines = len(lines)
    
    # Adjust to 0-indexed
    cursor_idx = cursor_line - 1
    
    # Calculate context range
    start_idx = max(0, cursor_idx - context_lines_before)
    end_idx = min(total_lines, cursor_idx + context_lines_after)
    
    # Get context lines
    before_lines = lines[start_idx:cursor_idx]
    current_line = lines[cursor_idx] if cursor_idx < len(lines) else ""
    after_lines = lines[cursor_idx + 1:end_idx] if cursor_idx < len(lines) else []
    
    # Split current line at cursor
    cursor_col_idx = min(cursor_column - 1, len(current_line))
    before_cursor_text = current_line[:cursor_col_idx]
    after_cursor_text = current_line[cursor_col_idx:]
    
    # Combine context
    before_context = "\n".join(before_lines) + "\n" + before_cursor_text
    cursor_marker = "█"  # Visual marker for cursor position
    after_context = after_cursor_text + "\n" + "\n".join(after_lines)
    
    return before_context.strip(), cursor_marker, after_context.strip()


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


def get_related_code_from_repo(
    repo_dir: str,
    file_path: str,
    current_context: str,
    max_results: int = 3
) -> str:
    """
    Get related code from repository for better context.
    Uses semantic search to find similar code patterns.
    """
    try:
        # Get repo ID and load vector store
        repo_id = repo_id_from_path(repo_dir)
        store = FaissStore(repo_id, base_dir=f"{DATA_DIR}/index")
        
        if not store.index_path.exists():
            return ""
        
        store.load()
        
        # Create search query from current context
        # Extract key concepts from current code (last few lines)
        lines = current_context.splitlines()
        query_text = " ".join(lines[-5:])  # Use last 5 lines as query
        
        # Search for related code
        vec_results = store.query(query_text, k=TOP_K_EMB)
        
        # Filter out the current file to avoid duplication
        filtered_results = [r for r in vec_results if r.get("file") != file_path]
        
        # Limit results
        related_code_parts = []
        for result in filtered_results[:max_results]:
            file_path_rel = result.get("file", "")
            start = result.get("start", 0)
            end = result.get("end", 0)
            snippet = result.get("snippet", "")
            
            # Format as reference
            related_code_parts.append(f"File: {Path(file_path_rel).name} (lines {start}-{end})\n{snippet}\n")
        
        return "\n---\n".join(related_code_parts)
    
    except Exception as e:
        print(f"[code_completion] Error getting related code: {e}")
        return ""


def generate_completion(
    file_path: str,
    file_content: str,
    cursor_line: int,
    cursor_column: int,
    repo_dir: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 200
) -> str:
    """
    Generate code completion based on current context.
    
    Args:
        file_path: Path to the file being edited
        file_content: Full content of the file
        cursor_line: Cursor line number (1-indexed)
        cursor_column: Cursor column number (1-indexed)
        repo_dir: Optional repository directory for codebase context
        model: Optional model override
        temperature: Temperature for LLM generation (lower = more deterministic)
        max_tokens: Maximum tokens for completion
    
    Returns:
        Generated code completion string
    """
    try:
        # Extract code context
        before_cursor, cursor_marker, after_cursor = extract_code_context(
            file_content,
            cursor_line,
            cursor_column,
            context_lines_before=50,
            context_lines_after=20
        )
        
        # Get language
        language = get_language_from_file(file_path)
        
        # Get related code from codebase (optional, for better context)
        related_code = ""
        if repo_dir:
            related_code = get_related_code_from_repo(
                repo_dir,
                file_path,
                before_cursor + after_cursor,
                max_results=3
            )
        
        if not related_code:
            related_code = "(No related code found in codebase)"
        
        # Build prompt
        prompt = COMPLETION_PROMPT.format(
            file_path=file_path,
            language=language,
            line=cursor_line,
            column=cursor_column,
            before_cursor=before_cursor,
            cursor_marker=cursor_marker,
            after_cursor=after_cursor,
            related_code=related_code
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
        
        # Generate completion using LLM
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
                completion = message.content[0].text
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
                timeout=30  # Faster timeout for completions
            )
            completion = rsp.choices[0].message.content
        
        # Clean up completion (remove markdown code blocks if present)
        completion = completion.strip()
        
        # Remove markdown code blocks
        if completion.startswith("```"):
            # Remove opening code block
            lines = completion.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove closing code block
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            completion = "\n".join(lines)
        
        completion = completion.strip()
        
        return completion
    
    except Exception as e:
        print(f"[code_completion] Error generating completion: {e}")
        return ""


def generate_multiple_completions(
    file_path: str,
    file_content: str,
    cursor_line: int,
    cursor_column: int,
    repo_dir: Optional[str] = None,
    num_completions: int = 1,
    model: Optional[str] = None,
    temperature: float = 0.5  # Higher temperature for variety
) -> List[str]:
    """
    Generate multiple completion candidates.
    
    Args:
        Same as generate_completion
        num_completions: Number of completion candidates to generate
    
    Returns:
        List of completion strings
    """
    completions = []
    
    for i in range(num_completions):
        try:
            completion = generate_completion(
                file_path,
                file_content,
                cursor_line,
                cursor_column,
                repo_dir=repo_dir,
                model=model,
                temperature=temperature + (i * 0.1),  # Slight temperature variation
                max_tokens=200
            )
            
            if completion:
                completions.append(completion)
        except Exception as e:
            print(f"[code_completion] Error generating completion {i+1}: {e}")
            continue
    
    return completions


"""
Direct code editing module for editor-based AI editing.
Allows editing selected code directly in the editor with AI assistance.
"""
from typing import Dict, Optional, Tuple
from pathlib import Path
import re
import difflib
import json
import os

from backend.modules.llm_api import get_fresh_client
from backend.modules.search import ripgrep_candidates, fuse_results
from backend.modules.vector_store import FaissStore
from backend.modules.multi_repo import repo_id_from_path
from backend.modules.context_retriever import expand_code_context
from backend.config import (
    LLM_PROVIDER, LLM_MODEL, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY,
    DATA_DIR, TOP_K_EMB, TOP_K_FINAL
)


EDIT_PROMPT = """You are an expert code editor. Edit the selected code based on the user's instruction.

Instructions:
1. Understand the user's edit instruction carefully
2. Analyze the selected code and its context
3. Generate the edited version that:
   - Fulfills the user's request
   - Maintains code style and conventions
   - Preserves functionality unless explicitly requested to change
   - Is syntactically correct
   - Follows best practices
4. Only edit the selected code, preserve surrounding context
5. Return ONLY the edited code (no explanations, no markdown, just the code)

User's Edit Instruction: {instruction}

Selected Code:
```{language}
{selected_code}
```

File Context (surrounding code):
```{language}
{file_context}
```

Related Code from Codebase (if available):
{related_code}

Generate the edited version of the selected code. Return ONLY the edited code, nothing else."""


def generate_diff_text(old_code: str, new_code: str, file_path: str = "") -> str:
    """Generate unified diff text between old and new code."""
    old_lines = old_code.splitlines(keepends=True)
    new_lines = new_code.splitlines(keepends=True)
    
    diff = list(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{file_path}" if file_path else "a/original",
        tofile=f"b/{file_path}" if file_path else "b/edited",
        lineterm='',
        n=3  # Show 3 lines of context
    ))
    
    return "".join(diff)


def edit_code_directly(
    selected_code: str,
    instruction: str,
    file_path: str,
    repo_dir: Optional[str] = None,
    file_context: Optional[str] = None,
    language: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3
) -> Dict:
    """
    Edit selected code based on user instruction.
    
    Args:
        selected_code: The code snippet to edit
        instruction: Natural language instruction for editing
        file_path: Path to the file containing the code
        repo_dir: Optional repository directory for codebase context
        file_context: Optional surrounding code context
        language: Optional programming language (auto-detected from file extension)
        model: Optional model override
        temperature: Temperature for LLM generation
    
    Returns:
        Dict with edited_code, diff, and metadata
    """
    try:
        # Detect language from file extension if not provided
        if not language:
            file_ext = Path(file_path).suffix.lower()
            lang_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.tsx': 'typescript',
                '.jsx': 'javascript',
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
                '.sql': 'sql',
                '.sh': 'bash',
                '.bat': 'batch',
                '.ps1': 'powershell'
            }
            language = lang_map.get(file_ext, 'text')
        
        # Get codebase context if repo_dir provided
        related_code = ""
        if repo_dir:
            try:
                repo_id = repo_id_from_path(repo_dir)
                store = FaissStore(repo_id, base_dir=f"{DATA_DIR}/index")
                
                if store.index_path.exists():
                    store.load()
                    # Search for related code
                    search_query = f"{instruction} {selected_code[:100]}"
                    vec_results = store.query(search_query, k=min(TOP_K_EMB, 3))
                    
                    context_parts = []
                    for result in vec_results:
                        rel_file = result.get("file", "")
                        snippet = result.get("snippet", "")
                        # Only include if from different location to avoid duplication
                        if rel_file != file_path:
                            context_parts.append(f"File: {Path(rel_file).name}\n```\n{snippet[:300]}\n```\n")
                    
                    if context_parts:
                        related_code = "\n---\n".join(context_parts)
            except Exception as e:
                print(f"[direct_edit] Error getting codebase context: {e}")
                related_code = ""
        
        if not related_code:
            related_code = "(No related code found)"
        
        # Prepare file context
        if not file_context:
            file_context = "(No surrounding context provided)"
        
        # Build prompt
        prompt = EDIT_PROMPT.format(
            instruction=instruction,
            selected_code=selected_code,
            file_context=file_context[:1000],  # Limit context size
            language=language,
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
        
        print(f"[direct_edit] Editing code in {Path(file_path).name} based on: {instruction[:80]}...")
        
        # Generate edited code using LLM
        # Handle Anthropic separately
        if LLM_PROVIDER == "anthropic":
            try:
                from anthropic import Anthropic
                anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
                message = anthropic_client.messages.create(
                    model=model_to_use,
                    max_tokens=2000,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                edited_code = message.content[0].text
            except Exception as e:
                raise Exception(f"Anthropic API error: {str(e)}")
        else:
            # OpenAI-compatible providers
            api_client = get_fresh_client()
            rsp = api_client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=2000,
                timeout=180
            )
            edited_code = rsp.choices[0].message.content
        
        # Clean up the response (remove markdown code blocks if present)
        edited_code = edited_code.strip()
        
        # Remove markdown code blocks if present
        if "```" in edited_code:
            # Extract code from markdown code block
            code_block_match = re.search(r'```(?:{language})?\s*\n(.*?)\n```', edited_code, re.DOTALL)
            if code_block_match:
                edited_code = code_block_match.group(1)
            else:
                # Try simpler pattern
                lines = edited_code.splitlines()
                # Remove first line if it starts with ```
                if lines and lines[0].startswith('```'):
                    lines = lines[1:]
                # Remove last line if it's ```
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                edited_code = '\n'.join(lines)
        
        # Generate diff
        diff_text = generate_diff_text(selected_code, edited_code, Path(file_path).name)
        
        # Calculate line changes
        old_lines = selected_code.splitlines()
        new_lines = edited_code.splitlines()
        lines_added = len(new_lines) - len(old_lines)
        lines_removed = max(0, len(old_lines) - len(new_lines)) if lines_added >= 0 else 0
        
        return {
            "ok": True,
            "original_code": selected_code,
            "edited_code": edited_code,
            "diff": diff_text,
            "file_path": file_path,
            "language": language,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "instruction": instruction
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"[direct_edit] Error in edit_code_directly: {e}")
        import traceback
        traceback.print_exc()
        return {
            "ok": False,
            "error": error_msg,
            "original_code": selected_code,
            "edited_code": None
        }


def stream_edit_code_directly(
    selected_code: str,
    instruction: str,
    file_path: str,
    repo_dir: Optional[str] = None,
    file_context: Optional[str] = None,
    language: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3
):
    """
    Stream code editing for real-time output.
    Yields chunks of edited code as they are generated.
    
    Args:
        Same as edit_code_directly
    
    Yields:
        String chunks of edited code
    """
    try:
        # Validate input
        if not selected_code:
            yield "Error: selected_code is required"
            return
        
        if not instruction:
            yield "Error: instruction is required"
            return
        
        if not file_path:
            yield "Error: file_path is required"
            return
        
        # Detect language from file extension if not provided
        if not language:
            file_ext = Path(file_path).suffix.lower()
            lang_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.tsx': 'typescript',
                '.jsx': 'javascript',
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
                '.sql': 'sql',
                '.sh': 'bash',
                '.bat': 'batch',
                '.ps1': 'powershell'
            }
            language = lang_map.get(file_ext, 'text')
        
        # Get codebase context if repo_dir provided
        related_code = ""
        if repo_dir:
            try:
                repo_id = repo_id_from_path(repo_dir)
                store = FaissStore(repo_id, base_dir=f"{DATA_DIR}/index")
                
                if store.index_path.exists():
                    store.load()
                    # Search for related code
                    search_query = f"{instruction} {selected_code[:100]}"
                    vec_results = store.query(search_query, k=min(TOP_K_EMB, 3))
                    
                    context_parts = []
                    for result in vec_results:
                        rel_file = result.get("file", "")
                        snippet = result.get("snippet", "")
                        # Only include if from different location to avoid duplication
                        if rel_file != file_path:
                            context_parts.append(f"File: {Path(rel_file).name}\n```\n{snippet[:300]}\n```\n")
                    
                    if context_parts:
                        related_code = "\n---\n".join(context_parts)
            except Exception as e:
                print(f"[direct_edit] Error getting codebase context: {e}")
                related_code = ""
        
        if not related_code:
            related_code = "(No related code found)"
        
        # Prepare file context
        if not file_context:
            file_context = "(No surrounding context provided)"
        
        # Build prompt
        prompt = EDIT_PROMPT.format(
            instruction=instruction,
            selected_code=selected_code,
            file_context=file_context[:1000],  # Limit context size
            language=language,
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
        
        print(f"[direct_edit] Streaming edit for {Path(file_path).name} based on: {instruction[:80]}...")
        
        # Streaming only works with OpenAI-compatible APIs
        if LLM_PROVIDER == "anthropic":
            # Anthropic streaming would need separate implementation
            # For now, fall back to non-streaming
            result = edit_code_directly(
                selected_code=selected_code,
                instruction=instruction,
                file_path=file_path,
                repo_dir=repo_dir,
                file_context=file_context,
                language=language,
                model=model,
                temperature=temperature
            )
            if result.get("ok"):
                edited_code = result.get("edited_code", "")
                # Yield in chunks to simulate streaming
                for i in range(0, len(edited_code), 100):
                    yield edited_code[i:i+100]
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
                max_tokens=2000,
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


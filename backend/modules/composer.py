"""
Multi-file editing module (Composer Mode).
Similar to Cursor's Composer - allows editing multiple files simultaneously through natural language.
"""
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
import re
import difflib
import json
from datetime import datetime

from backend.modules.llm_api import get_fresh_client
from backend.modules.search import ripgrep_candidates, fuse_results
from backend.modules.vector_store import FaissStore
from backend.modules.multi_repo import repo_id_from_path
from backend.config import LLM_PROVIDER, LLM_MODEL, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, DATA_DIR, TOP_K_EMB
import os


COMPOSER_PROMPT = """You are an expert code editor. You will edit multiple files based on the user's natural language instructions.

Instructions:
1. Analyze the user's request carefully
2. Identify which files need to be edited
3. Understand the codebase structure and dependencies
4. Generate edits that:
   - Are syntactically correct
   - Maintain consistency across files
   - Preserve existing functionality
   - Follow the codebase patterns and style
   - Handle dependencies between files correctly
5. Return edits in a structured format

User Request: {request}

Target Files: {target_files}

Codebase Context:
{codebase_context}

Generate the edits for each file. For each file, provide:
1. The file path
2. The complete edited content OR
3. A list of specific edits (insert/delete/replace) with line numbers

Return your response in JSON format with this structure:
{{
    "edits": [
        {{
            "file": "path/to/file.py",
            "action": "replace",  // or "create", "delete", "modify"
            "content": "complete file content after edit",
            "changes": [
                {{"type": "replace", "start_line": 10, "end_line": 15, "old": "...", "new": "..."}},
                {{"type": "insert", "line": 20, "content": "..."}},
                {{"type": "delete", "start_line": 25, "end_line": 30}}
            ],
            "description": "What was changed in this file"
        }}
    ],
    "dependencies": ["file1.py", "file2.py"],  // Files that depend on each other
    "summary": "Summary of all changes"
}}

Important: Only modify what's necessary. Preserve as much existing code as possible."""


def get_file_content(file_path: Path) -> str:
    """Read file content safely."""
    try:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"[composer] Error reading file {file_path}: {e}")
        return ""


def generate_diff(old_content: str, new_content: str, file_path: str) -> List[Dict]:
    """
    Generate a unified diff between old and new content.
    Returns list of diff operations.
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = list(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm=''
    ))
    
    # Parse diff into structured format
    changes = []
    current_change = None
    
    for line in diff:
        if line.startswith("@@"):
            # Start of a new hunk
            match = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
            if match:
                old_start = int(match.group(1))
                old_count = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_count = int(match.group(4)) if match.group(4) else 1
                
                if current_change:
                    changes.append(current_change)
                
                current_change = {
                    "old_start": old_start,
                    "old_count": old_count,
                    "new_start": new_start,
                    "new_count": new_count,
                    "lines": []
                }
        elif current_change and line.startswith((" ", "-", "+")):
            # Content line
            current_change["lines"].append({
                "type": "context" if line.startswith(" ") else ("removed" if line.startswith("-") else "added"),
                "content": line[1:] if line.startswith((" ", "-", "+")) else line
            })
    
    if current_change:
        changes.append(current_change)
    
    return changes


def validate_file_paths(file_paths: List[str], repo_dir: str) -> Tuple[bool, List[str]]:
    """Validate that all file paths exist or can be created."""
    repo_path = Path(repo_dir)
    errors = []
    
    for file_path in file_paths:
        file_full_path = repo_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
        parent_dir = file_full_path.parent
        
        # Check if parent directory exists (for new files)
        if not file_full_path.exists() and not parent_dir.exists():
            errors.append(f"Parent directory does not exist for {file_path}")
        
        # Check if file is within repo directory (security)
        try:
            file_full_path.resolve().relative_to(repo_path.resolve())
        except ValueError:
            errors.append(f"File path {file_path} is outside repository directory")
    
    return len(errors) == 0, errors


def compose_multi_file_edit(
    request: str,
    repo_dir: str,
    target_files: Optional[List[str]] = None,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 4000
) -> Dict:
    """
    Compose multi-file edits based on natural language request.
    
    Args:
        request: Natural language description of changes
        repo_dir: Repository directory
        target_files: Optional list of specific files to edit (if None, AI determines)
        model: Optional model override
        temperature: Temperature for LLM generation
        max_tokens: Maximum tokens for generation
    
    Returns:
        Dict with edits, diffs, and metadata
    """
    try:
        repo_path = Path(repo_dir)
        if not repo_path.exists():
            return {
                "ok": False,
                "error": f"Repository not found: {repo_dir}"
            }
        
        # Get codebase context
        codebase_context = ""
        try:
            repo_id = repo_id_from_path(repo_dir)
            store = FaissStore(repo_id, base_dir=f"{DATA_DIR}/index")
            
            if store.index_path.exists():
                store.load()
                vec_results = store.query(request, k=TOP_K_EMB)
                context_parts = []
                for result in vec_results[:5]:
                    file_path = result.get("file", "")
                    snippet = result.get("snippet", "")
                    context_parts.append(f"File: {Path(file_path).name}\n{snippet}\n")
                codebase_context = "\n---\n".join(context_parts)
        except Exception as e:
            print(f"[composer] Error getting codebase context: {e}")
        
        if not codebase_context:
            codebase_context = "(No codebase context available)"
        
        # Get current file contents if target_files specified
        file_contents = {}
        if target_files:
            for file_path in target_files:
                full_path = repo_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
                if full_path.exists():
                    file_contents[file_path] = get_file_content(full_path)
                else:
                    file_contents[file_path] = ""  # New file
        
        # Build prompt
        target_files_str = ", ".join(target_files) if target_files else "AI will determine which files to edit"
        prompt = COMPOSER_PROMPT.format(
            request=request,
            target_files=target_files_str,
            codebase_context=codebase_context
        )
        
        # Add current file contents to prompt if available
        if file_contents:
            prompt += "\n\nCurrent File Contents:\n"
            for file_path, content in file_contents.items():
                prompt += f"\n--- File: {file_path} ---\n{content[:2000]}...\n"  # Limit per file
        
        # Model selection
        if model:
            model_to_use = model
        elif os.getenv("LLM_MODEL"):
            model_to_use = os.getenv("LLM_MODEL")
        elif LLM_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY and os.getenv("OPENAI_MODEL"):
            model_to_use = os.getenv("OPENAI_MODEL")
        else:
            model_to_use = LLM_MODEL
        
        print(f"[composer] Generating multi-file edits for: {request[:80]}...")
        
        # Generate edits using LLM
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
                response_text = message.content[0].text
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
            response_text = rsp.choices[0].message.content
        
        # Parse JSON response
        response_text = response_text.strip()
        
        # Extract JSON if wrapped in markdown code blocks
        if "```json" in response_text:
            json_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
        elif "```" in response_text:
            json_match = re.search(r'```\s*\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
        
        try:
            edits_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"[composer] Failed to parse JSON response: {e}")
            print(f"[composer] Raw response: {response_text[:500]}...")
            # Fallback: try to extract edits manually
            return {
                "ok": False,
                "error": f"Failed to parse LLM response as JSON: {e}",
                "raw_response": response_text[:1000]
            }
        
        # Process edits and generate diffs
        processed_edits = []
        all_diffs = []
        
        for edit in edits_data.get("edits", []):
            file_path = edit.get("file")
            action = edit.get("action", "modify")
            new_content = edit.get("content", "")
            changes = edit.get("changes", [])
            description = edit.get("description", "")
            
            if not file_path:
                continue
            
            # Get current file content
            full_path = repo_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
            old_content = get_file_content(full_path) if full_path.exists() else ""
            
            # If new_content provided, use it; otherwise reconstruct from changes
            if new_content:
                final_content = new_content
            elif changes:
                # Reconstruct from changes (simplified - in production, apply changes properly)
                final_content = old_content  # Placeholder
            else:
                final_content = old_content  # No changes
            
            # Generate diff
            diff_text = ""
            if old_content or final_content:
                diff_ops = generate_diff(old_content, final_content, file_path)
                # Convert to unified diff format
                diff_lines = []
                for op in diff_ops:
                    diff_lines.append(f"@@ -{op['old_start']},{op['old_count']} +{op['new_start']},{op['new_count']} @@")
                    for line in op['lines']:
                        prefix = {"context": " ", "removed": "-", "added": "+"}.get(line['type'], " ")
                        diff_lines.append(prefix + line['content'])
                diff_text = "\n".join(diff_lines)
            
            processed_edit = {
                "file": file_path,
                "action": action,
                "old_content": old_content,
                "new_content": final_content,
                "diff": diff_text,
                "description": description,
                "changes": changes if changes else None,
                "lines_added": len(final_content.splitlines()) - len(old_content.splitlines()) if old_content else len(final_content.splitlines()),
                "lines_removed": len(old_content.splitlines()) - len(final_content.splitlines()) if old_content else 0
            }
            
            processed_edits.append(processed_edit)
            all_diffs.append(diff_text)
        
        # Validate file paths
        file_paths = [edit["file"] for edit in processed_edits]
        paths_valid, path_errors = validate_file_paths(file_paths, repo_dir)
        
        return {
            "ok": True,
            "edits": processed_edits,
            "dependencies": edits_data.get("dependencies", []),
            "summary": edits_data.get("summary", ""),
            "total_files": len(processed_edits),
            "paths_valid": paths_valid,
            "path_errors": path_errors,
            "request": request,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"[composer] Error in compose_multi_file_edit: {e}")
        import traceback
        traceback.print_exc()
        return {
            "ok": False,
            "error": error_msg,
            "edits": []
        }


def apply_edits(edits: List[Dict], repo_dir: str, dry_run: bool = False) -> Dict:
    """
    Apply edits to files.
    
    Args:
        edits: List of edit dictionaries from compose_multi_file_edit
        repo_dir: Repository directory
        dry_run: If True, don't actually apply changes (just validate)
    
    Returns:
        Dict with results of applying edits
    """
    repo_path = Path(repo_dir)
    results = []
    errors = []
    
    for edit in edits:
        file_path = edit.get("file")
        new_content = edit.get("new_content", "")
        action = edit.get("action", "modify")
        
        if not file_path:
            errors.append("Missing file path in edit")
            continue
        
        full_path = repo_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
        
        try:
            if action == "delete":
                if not dry_run and full_path.exists():
                    full_path.unlink()
                results.append({
                    "file": file_path,
                    "action": "deleted",
                    "success": True
                })
            elif action == "create" or (action == "modify" and not full_path.exists()):
                # Create new file
                if not dry_run:
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(new_content, encoding="utf-8")
                results.append({
                    "file": file_path,
                    "action": "created",
                    "success": True,
                    "lines": len(new_content.splitlines())
                })
            else:
                # Modify existing file
                if not dry_run:
                    full_path.write_text(new_content, encoding="utf-8")
                results.append({
                    "file": file_path,
                    "action": "modified",
                    "success": True,
                    "lines_added": edit.get("lines_added", 0),
                    "lines_removed": edit.get("lines_removed", 0)
                })
        except Exception as e:
            error_msg = f"Error applying edit to {file_path}: {str(e)}"
            errors.append(error_msg)
            results.append({
                "file": file_path,
                "action": action,
                "success": False,
                "error": error_msg
            })
    
    return {
        "ok": len(errors) == 0,
        "results": results,
        "errors": errors,
        "dry_run": dry_run,
        "files_changed": len([r for r in results if r.get("success")])
    }


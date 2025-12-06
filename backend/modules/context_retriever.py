"""
Enhanced context retrieval for code analysis.
Expands code snippets with surrounding context, imports, and related code.
"""
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
import re

# Import smart context functions (optional - for enhanced features)
try:
    from backend.modules.smart_context import (
        smart_expand_context,
        prioritize_context,
        filter_irrelevant_code,
        SMART_CONTEXT_AVAILABLE
    )
except ImportError:
    SMART_CONTEXT_AVAILABLE = False
    smart_expand_context = None
    prioritize_context = None
    filter_irrelevant_code = None

def expand_code_context(
    evidences: List[Dict],
    repo_dir: str,
    context_lines: int = 10,
    use_smart_context: bool = True,
    query: Optional[str] = None,
    file_path: Optional[str] = None,
    max_tokens: int = 8000
) -> List[Dict]:
    """
    Expand code snippets with surrounding context.
    Optionally uses smart context management for better prioritization.
    
    Args:
        evidences: List of evidence dicts with 'file', 'start', 'end', 'snippet' keys
        repo_dir: Root directory of repository
        context_lines: Number of lines to expand before/after
        use_smart_context: Whether to use smart context prioritization (default: True)
        query: Optional query string for relevance scoring (used with smart context)
        file_path: Optional target file path for prioritization (used with smart context)
        max_tokens: Maximum tokens to include (used with smart context)
    
    Returns:
        Enhanced evidences with expanded context, imports, and better boundaries
    """
    # Use smart context if available and enabled
    if use_smart_context and SMART_CONTEXT_AVAILABLE and smart_expand_context:
        return smart_expand_context(
            evidences,
            repo_dir=repo_dir,
            query=query,
            file_path=file_path,
            max_tokens=max_tokens,
            context_lines=context_lines,
            exclude_irrelevant=True,
            prioritize_recent=True,
            use_sliding_window=False  # Can be enabled for very large files
        )
    
    # Fallback to original implementation
    if not evidences:
        return evidences
    
    repo_path = Path(repo_dir)
    enhanced = []
    
    for evidence in evidences:
        file_path = Path(evidence["file"])
        
        # Make path absolute if relative
        if not file_path.is_absolute():
            file_path = repo_path / file_path
        
        if not file_path.exists():
            # File doesn't exist, return original
            enhanced.append(evidence)
            continue
        
        try:
            # Read the full file
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            total_lines = len(lines)
            
            # Get original boundaries
            start = max(1, evidence.get("start", 1))
            end = min(total_lines, evidence.get("end", start))
            
            # Expand boundaries to include more context
            expanded_start = max(1, start - context_lines)
            expanded_end = min(total_lines, end + context_lines)
            
            # Try to expand to function/class boundaries if possible
            expanded_start, expanded_end = expand_to_semantic_boundaries(
                lines, expanded_start, expanded_end, file_path
            )
            
            # Get imports if we're not already at the top
            imports = get_imports(lines, file_path) if expanded_start > 20 else []
            
            # Build enhanced snippet
            snippet_lines = lines[expanded_start - 1:expanded_end]
            snippet = "\n".join(snippet_lines)
            
            # Add imports if found and not already in snippet
            if imports and expanded_start > len(imports) + 5:
                imports_text = "\n".join(imports)
                snippet = f"{imports_text}\n\n{snippet}"
                # Adjust start to account for imports
                expanded_start = max(1, expanded_start - len(imports))
            
            # Create enhanced evidence
            enhanced_evidence = evidence.copy()
            enhanced_evidence.update({
                "file": str(file_path),
                "start": expanded_start,
                "end": expanded_end,
                "snippet": snippet,
                "original_start": start,
                "original_end": end,
                "has_imports": bool(imports and expanded_start > len(imports) + 5)
            })
            
            enhanced.append(enhanced_evidence)
            
        except Exception as e:
            # If we can't enhance, return original
            print(f"[context_retriever] Error enhancing {file_path}: {e}")
            enhanced.append(evidence)
    
    return enhanced


def expand_to_semantic_boundaries(
    lines: List[str], start: int, end: int, file_path: Path
) -> Tuple[int, int]:
    """
    Expand code snippet to natural boundaries (function/class start/end).
    
    Args:
        lines: All lines of the file
        start: Current start line (1-indexed)
        end: Current end line (1-indexed)
        file_path: Path to the file for extension detection
    
    Returns:
        (new_start, new_end) with expanded boundaries
    """
    ext = file_path.suffix.lower()
    
    # Try to find function/class boundaries
    if ext == '.py':
        return expand_python_boundaries(lines, start, end)
    elif ext in ['.js', '.ts', '.jsx', '.tsx']:
        return expand_js_boundaries(lines, start, end)
    else:
        # For other languages, just return as-is with slight expansion
        return (max(1, start - 3), min(len(lines), end + 3))


def expand_python_boundaries(lines: List[str], start: int, end: int) -> Tuple[int, int]:
    """Expand Python code to function/class boundaries."""
    # Look backwards for function/class definition
    new_start = start
    for i in range(start - 1, max(0, start - 50), -1):
        line = lines[i].strip()
        # Check for function or class definition
        if re.match(r'^(def|class|async def)\s+', line):
            new_start = i + 1  # Convert to 1-indexed
            break
        # Stop at module-level comments/docstrings
        if line.startswith('#') or line.startswith('"""') or line.startswith("'''"):
            if i < start - 3:
                break
    
    # Look forwards for end of function/class
    new_end = end
    indent_level = len(lines[start - 1]) - len(lines[start - 1].lstrip())
    
    for i in range(end, min(len(lines), end + 100)):
        if i >= len(lines):
            new_end = len(lines)
            break
        
        line = lines[i]
        line_indent = len(line) - len(line.lstrip())
        
        # If we hit something at same or less indent and it's not empty/comments
        if line.strip() and not line.strip().startswith('#') and line_indent <= indent_level:
            # Check if it's a new definition
            if re.match(r'^\s*(def|class|async def)\s+', line):
                new_end = i  # End before this new definition
                break
            # If we're at module level (indent 0), stop
            if line_indent == 0:
                new_end = i
                break
    
    return (new_start, new_end)


def expand_js_boundaries(lines: List[str], start: int, end: int) -> Tuple[int, int]:
    """Expand JavaScript/TypeScript code to function/class boundaries."""
    # Look backwards for function/class definition
    new_start = start
    func_patterns = [
        r'^\s*(export\s+)?(default\s+)?(function|class|const|let|var)\s+\w+',
        r'^\s*(export\s+)?(const|let|var)\s+\w+\s*=\s*(async\s+)?\([^)]*\)\s*=>',
        r'^\s*(export\s+)?(const|let|var)\s+\w+\s*=\s*(async\s+)?function',
    ]
    
    for i in range(start - 1, max(0, start - 50), -1):
        line = lines[i]
        if any(re.search(p, line) for p in func_patterns):
            new_start = i + 1  # Convert to 1-indexed
            break
    
    # Look forwards for end using brace counting
    new_end = end
    brace_count = 0
    in_function = False
    
    for i in range(start - 1, min(len(lines), end + 200)):
        line = lines[i]
        brace_count += line.count('{') - line.count('}')
        
        if brace_count > 0:
            in_function = True
        
        # If we closed all braces and were in a function
        if in_function and brace_count == 0:
            new_end = i + 1
            break
        
        # Check for new function/class at same level (module level)
        if in_function and brace_count == 0:
            if any(re.search(p, line) for p in func_patterns):
                new_end = i
                break
    
    return (new_start, min(len(lines), new_end))


def get_imports(lines: List[str], file_path: Path) -> List[str]:
    """
    Extract import statements from the beginning of a file.
    
    Args:
        lines: All lines of the file
        file_path: Path to file for extension detection
    
    Returns:
        List of import lines (first 30 lines or until first non-import)
    """
    imports = []
    ext = file_path.suffix.lower()
    
    # Pattern for imports (Python or JS/TS)
    if ext == '.py':
        import_pattern = re.compile(r'^(import|from)\s+')
    elif ext in ['.js', '.ts', '.jsx', '.tsx']:
        import_pattern = re.compile(r'^(import|export\s+.*from|const.*require)')
    else:
        return imports
    
    # Get imports from first 30 lines
    for i, line in enumerate(lines[:30]):
        stripped = line.strip()
        # Skip empty lines and comments at the start
        if not stripped:
            continue
        if stripped.startswith('#'):
            continue
        
        # Check if it's an import
        if import_pattern.match(stripped):
            imports.append(line.rstrip())
        elif imports and stripped:
            # We had imports but now hit non-import, stop
            break
    
    return imports


def enrich_with_related_code(
    evidences: List[Dict], repo_dir: str
) -> List[Dict]:
    """
    Add related code snippets (called functions, used classes) to evidences.
    
    Args:
        evidences: List of evidence dicts
        repo_dir: Root directory of repository
    
    Returns:
        Enhanced evidences with related code added
    """
    # TODO: Implement cross-reference finding
    # For now, just return enhanced evidences
    # Future: Find function calls in evidences, locate their definitions
    
    return evidences


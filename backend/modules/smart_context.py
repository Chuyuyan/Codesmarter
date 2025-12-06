"""
Smart Context Window Management
Intelligently manages context window size and prioritizes relevant code.
"""
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
import re
import os
from datetime import datetime, timedelta
# Note: We import expand_code_context inside smart_expand_context to avoid circular import

# Export flag for availability checking
SMART_CONTEXT_AVAILABLE = True


# Patterns for irrelevant code (to exclude)
IRRELEVANT_PATTERNS = {
    'python': [
        r'^#.*$',  # Comments
        r'^""".*?"""$',  # Docstrings (single line)
        r"^'''.*?'''$",  # Docstrings (single line)
        r'^import\s+',  # Imports (handled separately)
        r'^from\s+.*\s+import',  # From imports
        r'^__all__\s*=',  # __all__ declarations
        r'^#\s*pylint:',  # Pylint comments
        r'^#\s*type:',  # Type comments
    ],
    'javascript': [
        r'^//.*$',  # Comments
        r'^/\*.*?\*/$',  # Block comments
        r'^import\s+',  # Imports
        r'^export\s+',  # Exports (handled separately)
        r'^const\s+__.*__',  # Internal constants
    ],
    'typescript': [
        r'^//.*$',  # Comments
        r'^/\*.*?\*/$',  # Block comments
        r'^import\s+',  # Imports
        r'^export\s+',  # Exports
        r'^///\s*<reference',  # TypeScript references
    ]
}

# Code patterns that indicate high relevance
RELEVANT_PATTERNS = {
    'python': [
        r'^def\s+\w+',  # Function definitions
        r'^class\s+\w+',  # Class definitions
        r'^async\s+def\s+\w+',  # Async functions
        r'@\w+',  # Decorators
        r'if\s+__name__\s*==',  # Main block
    ],
    'javascript': [
        r'^(export\s+)?(default\s+)?(function|class|const|let|var)\s+\w+',  # Definitions
        r'^\s*(export\s+)?(const|let|var)\s+\w+\s*=\s*(async\s+)?\(',  # Arrow functions
        r'@\w+',  # Decorators (TypeScript/JSX)
    ],
    'typescript': [
        r'^(export\s+)?(default\s+)?(function|class|interface|type|enum)\s+\w+',  # Definitions
        r'^\s*(export\s+)?(const|let|var)\s+\w+\s*:\s*\w+',  # Typed declarations
    ]
}


def prioritize_context(
    evidences: List[Dict],
    query: Optional[str] = None,
    file_path: Optional[str] = None,
    max_tokens: int = 8000,
    exclude_irrelevant: bool = True,
    prioritize_recent: bool = True
) -> List[Dict]:
    """
    Intelligently prioritize and filter code context.
    
    Args:
        evidences: List of evidence dicts with 'file', 'start', 'end', 'snippet' keys
        query: Optional query string for relevance scoring
        file_path: Optional file path to prioritize
        max_tokens: Maximum tokens to include (rough estimate: 1 token ≈ 4 chars)
        exclude_irrelevant: Whether to exclude irrelevant code patterns
        prioritize_recent: Whether to prioritize recently edited files
    
    Returns:
        Prioritized and filtered evidences
    """
    if not evidences:
        return evidences
    
    # Score each evidence by relevance
    scored_evidences = []
    for evidence in evidences:
        score = calculate_relevance_score(
            evidence,
            query=query,
            target_file=file_path,
            prioritize_recent=prioritize_recent
        )
        scored_evidences.append((score, evidence))
    
    # Sort by score (highest first)
    scored_evidences.sort(key=lambda x: x[0], reverse=True)
    
    # Filter and limit by token budget
    prioritized = []
    total_chars = 0
    max_chars = max_tokens * 4  # Rough estimate: 1 token ≈ 4 chars
    
    for score, evidence in scored_evidences:
        snippet = evidence.get("snippet", "")
        
        # Filter irrelevant code if enabled
        if exclude_irrelevant:
            snippet = filter_irrelevant_code(snippet, evidence.get("file", ""))
            if not snippet.strip():
                continue  # Skip if all code was filtered out
            evidence = evidence.copy()
            evidence["snippet"] = snippet
        
        snippet_chars = len(snippet)
        
        # Check if we can fit this evidence
        if total_chars + snippet_chars <= max_chars:
            prioritized.append(evidence)
            total_chars += snippet_chars
        else:
            # Try to fit a truncated version
            remaining_chars = max_chars - total_chars
            if remaining_chars > 500:  # Only if we have meaningful space left
                truncated = truncate_snippet(snippet, remaining_chars)
                if truncated:
                    evidence = evidence.copy()
                    evidence["snippet"] = truncated
                    evidence["truncated"] = True
                    prioritized.append(evidence)
                    total_chars += len(truncated)
            break  # No more space
    
    return prioritized


def calculate_relevance_score(
    evidence: Dict,
    query: Optional[str] = None,
    target_file: Optional[str] = None,
    prioritize_recent: bool = True
) -> float:
    """
    Calculate relevance score for an evidence snippet.
    
    Returns:
        Score (higher = more relevant)
    """
    score = 1.0  # Base score
    
    file_path = evidence.get("file", "")
    snippet = evidence.get("snippet", "")
    
    # Boost if it's the target file
    if target_file and file_path and Path(file_path).samefile(Path(target_file)):
        score += 10.0
    
    # Boost if query matches snippet
    if query:
        query_lower = query.lower()
        snippet_lower = snippet.lower()
        
        # Exact phrase match
        if query_lower in snippet_lower:
            score += 5.0
        
        # Word matches
        query_words = set(query_lower.split())
        snippet_words = set(snippet_lower.split())
        common_words = query_words.intersection(snippet_words)
        if common_words:
            score += len(common_words) * 0.5
    
    # Boost for recently edited files
    if prioritize_recent:
        file_path_obj = Path(file_path)
        if file_path_obj.exists():
            try:
                mtime = file_path_obj.stat().st_mtime
                age_days = (datetime.now().timestamp() - mtime) / (24 * 3600)
                
                # Boost for files edited in last 7 days
                if age_days < 1:
                    score += 3.0
                elif age_days < 7:
                    score += 1.5
                elif age_days < 30:
                    score += 0.5
            except:
                pass
    
    # Boost for code with high-value patterns (functions, classes)
    language = detect_language(file_path)
    if language in RELEVANT_PATTERNS:
        for pattern in RELEVANT_PATTERNS[language]:
            if re.search(pattern, snippet, re.MULTILINE):
                score += 2.0
                break  # Only count once
    
    # Penalize very long snippets (prefer concise, focused code)
    snippet_lines = len(snippet.splitlines())
    if snippet_lines > 200:
        score -= 1.0
    if snippet_lines > 500:
        score -= 2.0
    
    return score


def filter_irrelevant_code(snippet: str, file_path: str) -> str:
    """
    Filter out irrelevant code patterns (comments, excessive imports, etc.).
    
    Args:
        snippet: Code snippet to filter
        file_path: Path to file for language detection
    
    Returns:
        Filtered snippet
    """
    language = detect_language(file_path)
    if language not in IRRELEVANT_PATTERNS:
        return snippet
    
    lines = snippet.splitlines()
    filtered_lines = []
    patterns = IRRELEVANT_PATTERNS[language]
    
    # Keep imports separately (they're useful but should be limited)
    import_lines = []
    max_imports = 10  # Limit imports
    
    for line in lines:
        stripped = line.strip()
        
        # Check if it's an import
        is_import = any(re.match(p, stripped) for p in patterns if 'import' in p or 'from' in p)
        if is_import:
            if len(import_lines) < max_imports:
                import_lines.append(line)
            continue  # Don't add to main code
        
        # Check if it matches irrelevant patterns
        is_irrelevant = any(re.match(p, stripped) for p in patterns if 'import' not in p and 'from' not in p)
        if is_irrelevant:
            continue  # Skip irrelevant lines
        
        # Keep the line
        filtered_lines.append(line)
    
    # Combine imports (if any) with filtered code
    if import_lines:
        result = "\n".join(import_lines) + "\n\n" + "\n".join(filtered_lines)
    else:
        result = "\n".join(filtered_lines)
    
    return result


def truncate_snippet(snippet: str, max_chars: int) -> str:
    """
    Intelligently truncate a snippet to fit within character limit.
    Tries to preserve function/class boundaries.
    
    Args:
        snippet: Code snippet to truncate
        max_chars: Maximum characters
    
    Returns:
        Truncated snippet with indicator
    """
    if len(snippet) <= max_chars:
        return snippet
    
    # Try to truncate at a natural boundary (function/class end)
    lines = snippet.splitlines()
    truncated_lines = []
    current_chars = 0
    
    for line in lines:
        line_chars = len(line) + 1  # +1 for newline
        
        if current_chars + line_chars > max_chars - 50:  # Leave room for truncation message
            # Check if we're in the middle of a function/class
            if any(re.search(r'^\s*(def|class|function|export)', line, re.IGNORECASE) for line in lines[len(truncated_lines):len(truncated_lines)+5]):
                # We're about to start a new function/class, good place to stop
                break
            # Otherwise, try to finish current line
            if current_chars + line_chars <= max_chars - 100:
                truncated_lines.append(line)
            break
        
        truncated_lines.append(line)
        current_chars += line_chars
    
    result = "\n".join(truncated_lines)
    if len(result) < len(snippet):
        result += f"\n\n// ... (truncated, showing {len(truncated_lines)} of {len(lines)} lines) ..."
    
    return result


def detect_language(file_path: str) -> str:
    """Detect programming language from file path."""
    if not file_path:
        return 'text'
    
    ext = Path(file_path).suffix.lower()
    lang_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
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
    return lang_map.get(ext, 'text')


def apply_sliding_window(
    evidences: List[Dict],
    window_size: int = 1000,
    overlap: int = 200
) -> List[Dict]:
    """
    Apply sliding window to very large code snippets.
    Useful for extremely large files that exceed token limits.
    
    Args:
        evidences: List of evidence dicts
        window_size: Size of each window in lines
        overlap: Overlap between windows in lines
    
    Returns:
        Evidences with sliding windows applied
    """
    windowed = []
    
    for evidence in evidences:
        snippet = evidence.get("snippet", "")
        lines = snippet.splitlines()
        
        # Only apply to very large snippets
        if len(lines) <= window_size:
            windowed.append(evidence)
            continue
        
        # Create sliding windows
        start = 0
        window_num = 0
        while start < len(lines):
            end = min(start + window_size, len(lines))
            window_lines = lines[start:end]
            window_snippet = "\n".join(window_lines)
            
            # Create new evidence for this window
            window_evidence = evidence.copy()
            window_evidence["snippet"] = window_snippet
            window_evidence["start"] = evidence.get("start", 1) + start
            window_evidence["end"] = evidence.get("start", 1) + end - 1
            window_evidence["window"] = window_num
            window_evidence["total_windows"] = (len(lines) + window_size - 1) // window_size
            
            windowed.append(window_evidence)
            
            # Move to next window with overlap
            start += window_size - overlap
            window_num += 1
    
    return windowed


def smart_expand_context(
    evidences: List[Dict],
    repo_dir: str,
    query: Optional[str] = None,
    file_path: Optional[str] = None,
    max_tokens: int = 8000,
    context_lines: int = 10,
    exclude_irrelevant: bool = True,
    prioritize_recent: bool = True,
    use_sliding_window: bool = False
) -> List[Dict]:
    """
    Smart context expansion with prioritization and filtering.
    Combines all smart context management features.
    
    Args:
        evidences: List of evidence dicts
        repo_dir: Repository directory
        query: Optional query for relevance scoring
        file_path: Optional target file path
        max_tokens: Maximum tokens to include
        context_lines: Lines to expand around code
        exclude_irrelevant: Filter irrelevant code
        prioritize_recent: Prioritize recently edited files
        use_sliding_window: Apply sliding window for very large files
    
    Returns:
        Enhanced evidences with smart context management
    """
    # Step 1: Expand context (existing functionality)
    # Import here to avoid circular dependency
    from backend.modules.context_retriever import expand_code_context as _expand_code_context
    # Call with use_smart_context=False to avoid recursion
    expanded = _expand_code_context(evidences, repo_dir, context_lines=context_lines, use_smart_context=False)
    
    # Step 2: Apply sliding window if needed
    if use_sliding_window:
        expanded = apply_sliding_window(expanded)
    
    # Step 3: Prioritize and filter
    prioritized = prioritize_context(
        expanded,
        query=query,
        file_path=file_path,
        max_tokens=max_tokens,
        exclude_irrelevant=exclude_irrelevant,
        prioritize_recent=prioritize_recent
    )
    
    return prioritized


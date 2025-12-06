from pathlib import Path
from typing import List, Dict, Set, Optional
import fnmatch
from backend.config import CHUNK_LINES, DEFAULT_IGNORE_PATTERNS

# Tree-sitter imports (optional - fallback if not available)
try:
    import tree_sitter
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    print("[parser] tree-sitter not available, using fallback line-based chunking")

def load_gitignore(root: Path) -> Set[str]:
    """Load patterns from .gitignore if it exists"""
    gitignore_path = root / ".gitignore"
    patterns = set(DEFAULT_IGNORE_PATTERNS)
    
    if gitignore_path.exists():
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith('#'):
                        # Normalize pattern
                        if not line.endswith('/'):
                            # Treat as both file and directory pattern
                            patterns.add(line)
                            patterns.add(line + '/')
                        else:
                            patterns.add(line)
        except Exception as e:
            print(f"[parser] Warning: Could not read .gitignore: {e}")
    
    return patterns

def should_ignore(path: Path, root: Path, ignore_patterns: Set[str]) -> bool:
    """Check if a path should be ignored based on patterns (similar to .gitignore logic)"""
    try:
        rel_path = path.relative_to(root)
        rel_str = str(rel_path).replace('\\', '/')
        parts = rel_str.split('/')
        
        # Check each pattern
        for pattern in ignore_patterns:
            pattern_clean = pattern.strip()
            if not pattern_clean:
                continue
            
            # Normalize pattern
            is_dir_pattern = pattern_clean.endswith('/')
            pattern_base = pattern_clean.rstrip('/')
            
            # Check each segment of the path
            for i in range(len(parts)):
                segment = parts[i]
                partial_path = '/'.join(parts[:i+1])
                
                # Exact match on segment
                if segment == pattern_base or fnmatch.fnmatch(segment, pattern_base):
                    return True
                
                # Directory pattern - match if path starts with pattern
                if is_dir_pattern and partial_path.startswith(pattern_base + '/'):
                    return True
                if is_dir_pattern and partial_path == pattern_base:
                    return True
                
                # Full path match
                if fnmatch.fnmatch(partial_path, pattern_base) or fnmatch.fnmatch(partial_path, pattern_clean):
                    return True
            
            # Full path match (for file patterns)
            if fnmatch.fnmatch(rel_str, pattern_base):
                return True
            
            # Match any part of the path
            if any(fnmatch.fnmatch(part, pattern_base) for part in parts):
                return True
        
        return False
    except ValueError:
        # Path is not relative to root (shouldn't happen, but handle gracefully)
        return False

def iter_text_files(root: Path, ignore_patterns: Set[str] = None):
    """
    Iterate over text files in the repository, excluding ignored patterns.
    
    Args:
        root: Root directory to scan
        ignore_patterns: Set of ignore patterns (defaults to loading from .gitignore + defaults)
    """
    if ignore_patterns is None:
        ignore_patterns = load_gitignore(root)
    
    exts = {".py",".js",".ts",".jsx",".tsx",".vue",".go",".java",".cs",".cpp",".c",".rs",".md"}
    
    # Track what we've seen to avoid duplicates
    seen_files = set()
    
    for p in root.rglob("*"):
        # Skip if already seen or if ignored
        if str(p) in seen_files:
            continue
            
        if should_ignore(p, root, ignore_patterns):
            continue
        
        # Check if it's a file with supported extension
        if p.is_file() and p.suffix.lower() in exts:
            seen_files.add(str(p))
            yield p

def get_language_parser(file_path: Path) -> Optional[Parser]:
    """Get appropriate tree-sitter parser for the file type"""
    if not TREE_SITTER_AVAILABLE:
        return None
    
    ext = file_path.suffix.lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'javascript',  # TypeScript uses JavaScript parser
        '.jsx': 'javascript',
        '.tsx': 'javascript',
    }
    
    lang_name = language_map.get(ext)
    if not lang_name:
        return None
    
    try:
        # Try to load language (this requires tree-sitter languages to be built)
        # For now, we'll use a simpler approach that works without building
        # In production, you'd build the languages first
        return None  # Will fallback to line-based for now
    except Exception as e:
        print(f"[parser] Could not load tree-sitter parser for {ext}: {e}")
        return None

def semantic_chunks(file_path: Path) -> List[Dict]:
    """
    Extract semantic chunks from code using pattern-based semantic extraction.
    Falls back to line-based chunking if semantic extraction fails.
    Note: Uses regex patterns for semantic extraction (works without tree-sitter).
    """
    ext = file_path.suffix.lower()
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    
    chunks = []
    
    # Use pattern-based semantic extraction (works without tree-sitter)
    if ext in ['.py', '.js', '.ts', '.jsx', '.tsx']:
        chunks = extract_semantic_units(file_path, text, lines, ext)
    
    # Fallback to line-based if semantic extraction didn't work
    if not chunks:
        return fallback_line_chunks(file_path)
    
    return chunks

def extract_semantic_units(file_path: Path, text: str, lines: List[str], ext: str) -> List[Dict]:
    """
    Extract semantic units (functions, classes, etc.) using regex patterns.
    This is a lightweight approach that works without tree-sitter language builds.
    """
    chunks = []
    file_str = str(file_path)
    
    # Patterns for different languages
    if ext == '.py':
        # Python: functions and classes
        import re
        # Match function definitions: def function_name(...):
        func_pattern = r'^(\s*)(def\s+\w+\s*\([^)]*\)\s*:.*)$'
        # Match class definitions: class ClassName(...):
        class_pattern = r'^(\s*)(class\s+\w+[^:]*:.*)$'
        
        current_chunk = None
        current_indent = -1
        
        for i, line in enumerate(lines, 1):
            func_match = re.match(func_pattern, line)
            class_match = re.match(class_pattern, line)
            
            if func_match or class_match:
                # Save previous chunk if exists
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Start new chunk
                indent = len(func_match.group(1) if func_match else class_match.group(1))
                current_chunk = {
                    "file": file_str,
                    "start": i,
                    "end": i,
                    "snippet": line,
                    "type": "class" if class_match else "function"
                }
                current_indent = indent
            elif current_chunk:
                # Continue current chunk
                if line.strip():  # Non-empty line
                    line_indent = len(line) - len(line.lstrip())
                    # If we hit something at same or less indent (and not empty), end chunk
                    if line_indent <= current_indent and line.strip() and not line.strip().startswith('#'):
                        current_chunk["end"] = i - 1
                        current_chunk["snippet"] = "\n".join(lines[current_chunk["start"]-1:current_chunk["end"]])
                        chunks.append(current_chunk)
                        current_chunk = None
                    else:
                        current_chunk["end"] = i
                else:
                    # Empty line - continue chunk
                    current_chunk["end"] = i
        
        # Add final chunk
        if current_chunk:
            current_chunk["snippet"] = "\n".join(lines[current_chunk["start"]-1:current_chunk["end"]])
            chunks.append(current_chunk)
    
    elif ext in ['.js', '.ts', '.jsx', '.tsx']:
        # JavaScript/TypeScript: functions, classes, arrow functions
        import re
        # Match function declarations (including React components)
        # Use search instead of match to be more flexible
        func_patterns = [
            r'export\s+default\s+function\s+\w+\s*\([^)]*\)\s*\{',  # export default function Component() {
            r'export\s+function\s+\w+\s*\([^)]*\)\s*\{',  # export function name() {
            r'(export\s+)?(async\s+)?function\s+\w+\s*\([^)]*\)\s*\{',  # function name() {
            r'(export\s+)?(const|let|var)\s+\w+\s*=\s*(async\s+)?\([^)]*\)\s*=>\s*\{',  # const name = () => {
            r'(export\s+)?(const|let|var)\s+\w+\s*=\s*(async\s+)?function\s*\([^)]*\)\s*\{',  # const name = function() {
            r'(export\s+)?(const|let|var)\s+\w+\s*=\s*\([^)]*\)\s*=>',  # const name = () => (JSX on next line)
        ]
        # Match class declarations
        class_pattern = r'(export\s+default\s+)?(export\s+)?class\s+\w+[^{]*\{'
        
        current_chunk = None
        brace_count = 0
        in_chunk = False
        
        for i, line in enumerate(lines, 1):
            # Check for function or class start (use search for flexibility)
            is_func = any(re.search(p, line) for p in func_patterns)
            is_class = re.search(class_pattern, line)
            
            if is_func or is_class:
                # Save previous chunk
                if current_chunk:
                    current_chunk["snippet"] = "\n".join(lines[current_chunk["start"]-1:current_chunk["end"]])
                    chunks.append(current_chunk)
                
                # Start new chunk
                current_chunk = {
                    "file": file_str,
                    "start": i,
                    "end": i,
                    "snippet": line,
                    "type": "class" if is_class else "function"
                }
                in_chunk = True
                brace_count = line.count('{') - line.count('}')
            elif current_chunk and in_chunk:
                # Track braces to find end of function/class
                brace_count += line.count('{') - line.count('}')
                current_chunk["end"] = i
                
                if brace_count == 0:
                    # End of function/class
                    current_chunk["snippet"] = "\n".join(lines[current_chunk["start"]-1:current_chunk["end"]])
                    chunks.append(current_chunk)
                    current_chunk = None
                    in_chunk = False
        
        # Add final chunk if exists
        if current_chunk:
            current_chunk["snippet"] = "\n".join(lines[current_chunk["start"]-1:current_chunk["end"]])
            chunks.append(current_chunk)
    
    # If we didn't find semantic units, return empty to trigger fallback
    if not chunks:
        return []
    
    return chunks

def fallback_line_chunks(file_path: Path, lines_per=CHUNK_LINES) -> List[Dict]:
    """Fallback: simple line-based chunking"""
    text = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    chunks = []
    start = 1
    while start <= len(text):
        end = min(start + lines_per - 1, len(text))
        snippet = "\n".join(text[start-1:end])
        chunks.append({
            "file": str(file_path),
            "start": start, "end": end,
            "snippet": snippet,
            "type": "lines"
        })
        start = end + 1
    return chunks

def slice_repo(repo_dir: str, use_semantic: bool = True) -> List[Dict]:
    """
    Slice repository into chunks.
    
    Args:
        repo_dir: Repository directory path
        use_semantic: If True, use semantic chunking (functions/classes). 
                     If False or semantic fails, fallback to line-based.
    """
    repo = Path(repo_dir)
    results = []
    semantic_count = 0
    fallback_count = 0
    
    for f in iter_text_files(repo):
        if use_semantic:
            chunks = semantic_chunks(f)
            # Check if we got semantic chunks (function/class) vs fallback (lines)
            if chunks:
                # Check if any chunk is semantic (not all are "lines")
                has_semantic = any(c.get("type") in ["function", "class"] for c in chunks)
                if has_semantic:
                    semantic_count += len(chunks)
                    results.extend(chunks)
                else:
                    # All chunks are "lines" type - semantic extraction didn't work
                    fallback_count += len(chunks)
                    results.extend(chunks)
            else:
                # No chunks returned - use fallback
                fallback_chunks = fallback_line_chunks(f)
                fallback_count += len(fallback_chunks)
                results.extend(fallback_chunks)
        else:
            fallback_chunks = fallback_line_chunks(f)
            fallback_count += len(fallback_chunks)
            results.extend(fallback_chunks)
    
    if use_semantic:
        print(f"[parser] Semantic chunks: {semantic_count}, Fallback chunks: {fallback_count}")
    
    return results

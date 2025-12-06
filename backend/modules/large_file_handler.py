"""
Utilities for handling large files in refactoring and analysis.
Provides better chunking strategies, streaming support, and edge case handling.
"""
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re
from backend.modules.parser import semantic_chunks, fallback_line_chunks


def chunk_large_file_semantically(
    file_path: Path,
    max_chunks: int = 5,
    max_lines_per_chunk: int = 200,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None
) -> List[Dict]:
    """
    Chunk a large file semantically (by functions/classes) for refactoring.
    
    Args:
        file_path: Path to the file
        max_chunks: Maximum number of chunks to return
        max_lines_per_chunk: Maximum lines per chunk
        start_line: Optional start line (1-indexed) - only chunk this range
        end_line: Optional end line (1-indexed) - only chunk this range
    
    Returns:
        List of chunk dicts with 'file', 'start', 'end', 'snippet', 'type' (function/class/etc)
    """
    if not file_path.exists():
        return []
    
    try:
        # Try semantic chunking first (functions/classes)
        chunks = semantic_chunks(file_path)
        
        if not chunks:
            # Fallback to line-based chunking
            chunks = fallback_line_chunks(file_path)
        
        # Filter by line range if specified
        if start_line or end_line:
            filtered_chunks = []
            for chunk in chunks:
                chunk_start = chunk.get("start", 1)
                chunk_end = chunk.get("end", chunk_start)
                
                # Check if chunk overlaps with requested range
                if start_line and chunk_end < start_line:
                    continue
                if end_line and chunk_start > end_line:
                    continue
                
                # Adjust chunk boundaries to fit within requested range
                if start_line and chunk_start < start_line:
                    chunk_start = start_line
                if end_line and chunk_end > end_line:
                    chunk_end = end_line
                
                # Re-extract snippet for adjusted range
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    lines = content.splitlines()
                    snippet_lines = lines[chunk_start - 1:chunk_end]
                    chunk["snippet"] = "\n".join(snippet_lines)
                    chunk["start"] = chunk_start
                    chunk["end"] = chunk_end
                except:
                    pass
                
                filtered_chunks.append(chunk)
            chunks = filtered_chunks
        
        # Limit chunk size
        limited_chunks = []
        for chunk in chunks[:max_chunks]:
            snippet = chunk.get("snippet", "")
            lines = snippet.splitlines()
            
            if len(lines) > max_lines_per_chunk:
                # Truncate but keep it as a semantic unit
                truncated_lines = lines[:max_lines_per_chunk]
                chunk["snippet"] = "\n".join(truncated_lines) + f"\n\n// ... (truncated, showing first {max_lines_per_chunk} of {len(lines)} lines) ..."
                chunk["end"] = chunk.get("start", 1) + max_lines_per_chunk - 1
                chunk["truncated"] = True
            else:
                chunk["truncated"] = False
            
            limited_chunks.append(chunk)
        
        return limited_chunks
    
    except Exception as e:
        print(f"[large_file_handler] Error chunking {file_path}: {e}")
        return []


def get_file_size_category(file_path: Path) -> str:
    """
    Categorize file size for appropriate handling strategy.
    
    Returns:
        "small" (< 200 lines), "medium" (200-1000), "large" (1000-5000), "very_large" (> 5000)
    """
    try:
        if not file_path.exists():
            return "unknown"
        
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        line_count = len(lines)
        
        if line_count < 200:
            return "small"
        elif line_count < 1000:
            return "medium"
        elif line_count < 5000:
            return "large"
        else:
            return "very_large"
    except:
        return "unknown"


def extract_specific_sections(
    file_path: Path,
    section_type: str = "function",
    max_sections: int = 5
) -> List[Dict]:
    """
    Extract specific sections (functions, classes) from a file for targeted refactoring.
    
    Args:
        file_path: Path to the file
        section_type: "function", "class", or "all"
        max_sections: Maximum number of sections to return
    
    Returns:
        List of section dicts
    """
    chunks = semantic_chunks(file_path)
    
    if not chunks:
        return []
    
    filtered = []
    for chunk in chunks:
        chunk_type = chunk.get("type", "").lower()
        
        if section_type == "all":
            filtered.append(chunk)
        elif section_type == "function" and "function" in chunk_type:
            filtered.append(chunk)
        elif section_type == "class" and "class" in chunk_type:
            filtered.append(chunk)
        
        if len(filtered) >= max_sections:
            break
    
    return filtered


def estimate_token_count(text: str) -> int:
    """
    Rough estimate of token count (for LLM context limits).
    Uses approximation: ~4 characters per token.
    """
    return len(text) // 4


def optimize_for_refactoring(
    evidences: List[Dict],
    max_total_tokens: int = 8000,  # Conservative estimate for refactoring
    prefer_semantic: bool = True
) -> List[Dict]:
    """
    Optimize code snippets for refactoring by:
    1. Using semantic chunking for large files
    2. Prioritizing relevant sections
    3. Respecting token limits
    
    Args:
        evidences: List of evidence dicts
        max_total_tokens: Maximum total tokens to send to LLM
        prefer_semantic: Whether to prefer semantic chunks over line-based
    
    Returns:
        Optimized list of evidences
    """
    optimized = []
    total_tokens = 0
    
    for ev in evidences:
        file_path = Path(ev.get("file", ""))
        
        if not file_path.exists():
            # Keep original if file doesn't exist
            optimized.append(ev)
            continue
        
        snippet = ev.get("snippet", "")
        snippet_tokens = estimate_token_count(snippet)
        
        # If snippet is small enough, keep it
        if snippet_tokens + total_tokens <= max_total_tokens:
            optimized.append(ev)
            total_tokens += snippet_tokens
            continue
        
        # For large snippets, try semantic chunking
        if prefer_semantic:
            chunks = chunk_large_file_semantically(
                file_path,
                max_chunks=3,
                max_lines_per_chunk=150,
                start_line=ev.get("start"),
                end_line=ev.get("end")
            )
            
            if chunks:
                # Use semantic chunks instead
                for chunk in chunks:
                    chunk_tokens = estimate_token_count(chunk.get("snippet", ""))
                    if chunk_tokens + total_tokens <= max_total_tokens:
                        optimized.append(chunk)
                        total_tokens += chunk_tokens
                    else:
                        # Truncate chunk to fit
                        remaining_tokens = max_total_tokens - total_tokens
                        if remaining_tokens > 500:  # Only if meaningful space
                            truncated = truncate_to_tokens(chunk, remaining_tokens)
                            optimized.append(truncated)
                            total_tokens += estimate_token_count(truncated.get("snippet", ""))
                        break
                continue
        
        # Fallback: truncate original snippet
        remaining_tokens = max_total_tokens - total_tokens
        if remaining_tokens > 500:
            truncated = truncate_to_tokens(ev, remaining_tokens)
            optimized.append(truncated)
            total_tokens += estimate_token_count(truncated.get("snippet", ""))
        else:
            break  # No more space
    
    return optimized


def truncate_to_tokens(evidence: Dict, max_tokens: int) -> Dict:
    """
    Truncate a code snippet to fit within token limit.
    Tries to preserve semantic boundaries (function/class boundaries).
    """
    snippet = evidence.get("snippet", "")
    lines = snippet.splitlines()
    
    # Estimate lines per token (rough)
    avg_chars_per_line = sum(len(line) for line in lines[:10]) / min(10, len(lines)) if lines else 50
    tokens_per_line = max(1, avg_chars_per_line // 4)
    max_lines = max(10, int(max_tokens / tokens_per_line))
    
    truncated_lines = lines[:max_lines]
    truncated_ev = evidence.copy()
    truncated_ev["snippet"] = "\n".join(truncated_lines) + f"\n\n// ... (truncated to ~{max_tokens} tokens, showing first {max_lines} of {len(lines)} lines) ..."
    truncated_ev["end"] = evidence.get("start", 1) + max_lines - 1
    truncated_ev["truncated"] = True
    
    return truncated_ev


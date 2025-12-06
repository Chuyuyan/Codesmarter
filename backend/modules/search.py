import subprocess, json
from pathlib import Path
from typing import List, Dict
from backend.config import TOP_K_RG, TOP_K_EMB

def ripgrep_candidates(query: str, repo_dir: str, top_k=TOP_K_RG) -> List[Dict]:
    """
    直接调用 rg，返回命中所在行号附近的短片段（降噪 + 近场）。
    rg 参数说明：
      -n 行号； -H 文件名； --no-heading 纯行； -S 大小写不敏感
      --iglob 用于排除文件模式
    """
    try:
        # Build ripgrep command with ignore patterns
        from backend.config import DEFAULT_IGNORE_PATTERNS
        
        rg = ["rg", "-nH", "-S", query, repo_dir]
        
        # Add ignore globs for common patterns
        ignore_globs = [
            "!node_modules/**",
            "!__pycache__/**",
            "!.git/**",
            "!.next/**",
            "!dist/**",
            "!build/**",
            "!.venv/**",
            "!venv/**",
            "!*.log",
        ]
        
        # Add ignore patterns
        for pattern in ignore_globs:
            rg.extend(["--iglob", pattern])
        
        out = subprocess.check_output(rg, text=True, errors="ignore")
    except Exception:
        return []
    hits = []
    for line in out.splitlines()[:top_k]:
        # Handle Windows paths: C:\path\to\file:line:content
        # Split from the right to handle paths with colons
        if ":" not in line:
            continue
        
        # Find the last two colons (line number and content separator)
        # Path might contain colons on Windows, so we split from the right
        last_colon = line.rfind(":")
        if last_colon == -1:
            continue
        
        second_last_colon = line.rfind(":", 0, last_colon)
        if second_last_colon == -1:
            continue
        
        path = line[:second_last_colon]
        try:
            lineno = int(line[second_last_colon + 1:last_colon])
        except ValueError:
            continue  # Skip if we can't parse line number
        content = line[last_colon + 1:]
        
        hits.append({"file": path, "lineno": lineno, "hit": content})
    return hits

def fuse_results(rg_hits: List[Dict], vec_hits: List[Dict], top_k=6) -> List[Dict]:
    """
    简单融合：如果 vec 命中文件在 rg 命中列表，加一点权重；同文件近场优先。
    """
    rg_files = {h["file"] for h in rg_hits}
    scored = []
    for v in vec_hits:
        bonus = 0.1 if v["file"] in rg_files else 0.0
        scored.append((v["score_vec"] + bonus, v))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:top_k]]


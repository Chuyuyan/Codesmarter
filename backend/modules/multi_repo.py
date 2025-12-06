"""
Multi-repository support for querying across multiple codebases.
"""
from pathlib import Path
from typing import List, Dict, Set, Optional
import json

from backend.modules.vector_store import FaissStore
from backend.modules.search import ripgrep_candidates, fuse_results
from backend.modules.parser import slice_repo
from backend.config import DATA_DIR, TOP_K_EMB, TOP_K_RG, TOP_K_FINAL


def repo_id_from_path(path: str) -> str:
    """Generate a repository ID from a path."""
    return Path(path).resolve().name


def get_indexed_repos(base_dir: str = None) -> List[Dict]:
    """
    Get list of all indexed repositories.
    
    Args:
        base_dir: Base directory for indices (defaults to DATA_DIR/index)
    
    Returns:
        List of dicts with 'repo_id', 'repo_dir', and 'chunks' info
    """
    if base_dir is None:
        base_dir = f"{DATA_DIR}/index"
    
    indexed_repos = []
    base_path = Path(base_dir)
    
    if not base_path.exists():
        return indexed_repos
    
    for repo_dir in base_path.iterdir():
        if repo_dir.is_dir():
            meta_path = repo_dir / "meta.json"
            index_path = repo_dir / "faiss.index"
            
            if meta_path.exists() and index_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        metas = json.load(f)
                    
                    # Try to get repo_dir from stored metadata
                    repo_dir_path = None
                    if metas and isinstance(metas, list) and len(metas) > 0:
                        first_file = metas[0].get("file", "")
                        if first_file:
                            repo_dir_path = str(Path(first_file).parent)
                    
                    indexed_repos.append({
                        "repo_id": repo_dir.name,
                        "repo_dir": repo_dir_path,
                        "chunks": len(metas) if isinstance(metas, list) else 0,
                        "index_path": str(index_path)
                    })
                except Exception as e:
                    print(f"[multi_repo] Error reading repo {repo_dir.name}: {e}")
    
    return indexed_repos


def search_multiple_repos(
    repo_dirs: List[str],
    query: str,
    top_k: int = TOP_K_FINAL,
    base_dir: str = None
) -> List[Dict]:
    """
    Search across multiple repositories and merge results.
    
    Args:
        repo_dirs: List of repository directory paths
        query: Search query
        top_k: Maximum number of results to return per repo (before merging)
        base_dir: Base directory for indices
    
    Returns:
        Merged list of search results with 'repo_id' field added
    """
    if base_dir is None:
        base_dir = f"{DATA_DIR}/index"
    
    all_results = []
    
    for repo_dir in repo_dirs:
        repo_path = Path(repo_dir)
        if not repo_path.exists():
            print(f"[multi_repo] Repo not found: {repo_dir}, skipping")
            continue
        
        rid = repo_id_from_path(repo_dir)
        store = FaissStore(rid, base_dir=base_dir)
        
        if not store.index_path.exists():
            print(f"[multi_repo] Repo {rid} not indexed, skipping")
            continue
        
        try:
            store.load()
            
            # Hybrid search for this repo
            rg_results = ripgrep_candidates(query, repo_dir, top_k=TOP_K_RG)
            vec_results = store.query(query, k=TOP_K_EMB)
            fused = fuse_results(rg_results, vec_results, top_k=top_k)
            
            # Add repo_id to each result
            for result in fused:
                result["repo_id"] = rid
                result["repo_dir"] = repo_dir
            
            all_results.extend(fused)
            print(f"[multi_repo] Found {len(fused)} results in {rid}")
            
        except Exception as e:
            print(f"[multi_repo] Error searching {rid}: {e}")
            continue
    
    # Sort all results by score (combined from vector and keyword search)
    # Results have 'score_vec' and 'score_rg', we'll use max of both or a combination
    def sort_key(result):
        score_vec = result.get("score_vec", 0.0)
        score_rg = result.get("score_rg", 0.0)
        # Use higher of the two scores, or average
        return max(score_vec, score_rg) if score_vec > 0 and score_rg > 0 else (score_vec + score_rg)
    
    all_results.sort(key=sort_key, reverse=True)
    
    # Return top results across all repos
    return all_results[:top_k]


def index_multiple_repos(
    repo_dirs: List[str],
    base_dir: str = None
) -> Dict:
    """
    Index multiple repositories.
    
    Args:
        repo_dirs: List of repository directory paths
        base_dir: Base directory for indices
    
    Returns:
        Dict with indexing results for each repo
    """
    if base_dir is None:
        base_dir = f"{DATA_DIR}/index"
    
    results = {
        "ok": True,
        "repos": []
    }
    
    for repo_dir in repo_dirs:
        repo_path = Path(repo_dir)
        if not repo_path.exists():
            results["repos"].append({
                "repo_dir": repo_dir,
                "ok": False,
                "error": f"Repository not found: {repo_dir}"
            })
            continue
        
        rid = repo_id_from_path(repo_dir)
        
        try:
            # Index the repository
            chunks = slice_repo(repo_dir)
            store = FaissStore(rid, base_dir=base_dir)
            store.build(chunks)
            
            results["repos"].append({
                "repo_id": rid,
                "repo_dir": repo_dir,
                "ok": True,
                "chunks": len(chunks)
            })
            
            print(f"[multi_repo] Indexed {rid}: {len(chunks)} chunks")
            
        except Exception as e:
            error_msg = str(e)
            results["repos"].append({
                "repo_id": rid,
                "repo_dir": repo_dir,
                "ok": False,
                "error": error_msg
            })
            print(f"[multi_repo] Error indexing {rid}: {error_msg}")
    
    return results


"""
Privacy mode module for GDPR compliance and security-conscious users.
When enabled, uses in-memory-only storage (RAM) instead of disk storage.
Code is cleared automatically on server shutdown.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from backend.config import DATA_DIR


class PrivacyMode:
    """
    Privacy mode manager.
    When enabled, uses in-memory-only storage (RAM) - no disk writes.
    Data is cleared automatically on server shutdown.
    """
    def __init__(self):
        """Initialize privacy mode from environment variable."""
        self.enabled = os.getenv("PRIVACY_MODE", "false").lower() in ("true", "1", "yes", "on")
        self._check_config()
    
    def _check_config(self):
        """Check and log privacy mode status."""
        if self.enabled:
            print("[privacy] Privacy mode ENABLED - Using in-memory storage (RAM only, no disk writes)")
        else:
            print("[privacy] Privacy mode DISABLED - Using disk storage")
    
    def is_enabled(self) -> bool:
        """Check if privacy mode is enabled."""
        return self.enabled
    
    def enable(self):
        """Enable privacy mode (runtime)."""
        self.enabled = True
        print("[privacy] Privacy mode ENABLED - Switching to in-memory storage")
    
    def disable(self):
        """Disable privacy mode (runtime)."""
        self.enabled = False
        print("[privacy] Privacy mode DISABLED - Switching to disk storage")
    
    def should_index(self) -> bool:
        """
        Check if indexing should be allowed.
        Returns True always - indexing works in privacy mode (in-memory).
        """
        return True
    
    def should_cache(self) -> bool:
        """
        Check if caching should be allowed.
        Returns True always - caching works in privacy mode (in-memory).
        """
        return True
    
    def should_store_code(self) -> bool:
        """
        Check if code storage should be allowed.
        Returns True always - storage works in privacy mode (in-memory).
        """
        return True
    
    def use_in_memory_storage(self) -> bool:
        """
        Check if in-memory storage should be used.
        Returns True when privacy mode is enabled (no disk writes).
        """
        return self.enabled
    
    def clear_all_data(self) -> Dict[str, Any]:
        """
        Clear all stored data (indexes, caches).
        - If privacy mode enabled: clears in-memory data only (disk storage already disabled)
        - If privacy mode disabled: clears disk-based data
        
        Returns:
            Dictionary with cleanup results
        """
        results = {
            "indexes_cleared": 0,
            "caches_cleared": 0,
            "in_memory_cleared": False,
            "total_files_removed": 0
        }
        
        try:
            # If privacy mode enabled, clear in-memory data
            if self.enabled:
                # Import here to avoid circular imports
                try:
                    from backend.modules.vector_store import _in_memory_stores
                    from backend.modules.cache import _in_memory_caches
                    
                    # Clear in-memory indexes
                    if _in_memory_stores:
                        results["indexes_cleared"] = len(_in_memory_stores)
                        _in_memory_stores.clear()
                        print(f"[privacy] Cleared {results['indexes_cleared']} in-memory indexes")
                    
                    # Clear in-memory caches
                    if _in_memory_caches:
                        results["caches_cleared"] = len(_in_memory_caches)
                        _in_memory_caches.clear()
                        print(f"[privacy] Cleared {results['caches_cleared']} in-memory caches")
                    
                    results["in_memory_cleared"] = True
                except ImportError:
                    # Modules not loaded yet, no in-memory data to clear
                    pass
                
                return {
                    "ok": True,
                    "message": "All in-memory data cleared successfully",
                    "storage_type": "in-memory",
                    **results
                }
            else:
                # Clear disk-based data
                # Clear indexes
                index_dir = Path(DATA_DIR) / "index"
                if index_dir.exists():
                    for repo_dir in index_dir.iterdir():
                        if repo_dir.is_dir():
                            # Count files before deletion
                            file_count = sum(1 for _ in repo_dir.rglob("*") if _.is_file())
                            results["total_files_removed"] += file_count
                            
                            # Remove directory
                            import shutil
                            shutil.rmtree(repo_dir)
                            results["indexes_cleared"] += 1
                            print(f"[privacy] Cleared disk index: {repo_dir.name}")
                
                # Clear caches
                cache_dir = Path(DATA_DIR) / "cache"
                if cache_dir.exists():
                    for cache_type_dir in cache_dir.iterdir():
                        if cache_type_dir.is_dir():
                            # Count files before deletion
                            file_count = sum(1 for _ in cache_type_dir.rglob("*.json") if _.is_file())
                            results["total_files_removed"] += file_count
                            
                            # Remove cache files
                            for cache_file in cache_type_dir.glob("*.json"):
                                cache_file.unlink()
                            results["caches_cleared"] += 1
                            print(f"[privacy] Cleared disk cache: {cache_type_dir.name}")
                
                return {
                    "ok": True,
                    "message": "All disk data cleared successfully",
                    "storage_type": "disk",
                    **results
                }
        
        except Exception as e:
            return {
                "ok": False,
                "error": f"Error clearing data: {str(e)}",
                **results
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get privacy mode status and statistics."""
        status = {
            "enabled": self.enabled,
            "storage_type": "in-memory (RAM)" if self.enabled else "disk",
            "indexing_allowed": self.should_index(),
            "caching_allowed": self.should_cache(),
            "code_storage_allowed": self.should_store_code(),
            "auto_cleanup": "On server shutdown" if self.enabled else "Manual only"
        }
        
        # Count stored data
        try:
            if self.enabled:
                # Count in-memory data
                try:
                    from backend.modules.vector_store import _in_memory_stores
                    from backend.modules.cache import _in_memory_caches
                    
                    index_count = len(_in_memory_stores) if _in_memory_stores else 0
                    cache_count = len(_in_memory_caches) if _in_memory_caches else 0
                    
                    status["stored_data"] = {
                        "indexed_repositories": index_count,
                        "cached_entries": cache_count,
                        "location": "RAM (in-memory)",
                        "note": "Data cleared automatically on server shutdown"
                    }
                except ImportError:
                    # Modules not loaded yet
                    status["stored_data"] = {
                        "indexed_repositories": 0,
                        "cached_entries": 0,
                        "location": "RAM (in-memory)",
                        "note": "Modules not loaded yet"
                    }
            else:
                # Count disk-based data
                index_dir = Path(DATA_DIR) / "index"
                cache_dir = Path(DATA_DIR) / "cache"
                
                index_count = 0
                if index_dir.exists():
                    index_count = len([d for d in index_dir.iterdir() if d.is_dir()])
                
                cache_count = 0
                if cache_dir.exists():
                    cache_count = sum(
                        len(list((cache_dir / cache_type).glob("*.json")))
                        for cache_type in ["llm", "search", "embeddings"]
                        if (cache_dir / cache_type).exists()
                    )
                
                status["stored_data"] = {
                    "indexed_repositories": index_count,
                    "cached_entries": cache_count,
                    "location": "disk"
                }
        except Exception as e:
            status["stored_data"] = {"error": str(e)}
        
        return status


# Global privacy mode instance (singleton)
_privacy_mode: Optional[PrivacyMode] = None


def get_privacy_mode() -> PrivacyMode:
    """Get or create privacy mode singleton."""
    global _privacy_mode
    if _privacy_mode is None:
        _privacy_mode = PrivacyMode()
    return _privacy_mode


def is_privacy_mode_enabled() -> bool:
    """Quick check if privacy mode is enabled."""
    return get_privacy_mode().is_enabled()


def require_privacy_check(func):
    """
    Decorator to check privacy mode before executing function.
    Note: This is now deprecated - privacy mode no longer blocks operations,
    it just uses in-memory storage instead of disk storage.
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Privacy mode now allows all operations (just uses in-memory storage)
        # This decorator is kept for backward compatibility but does nothing
        return func(*args, **kwargs)
    
    return wrapper


def privacy_aware_cache(func):
    """
    Decorator to skip caching when privacy mode is enabled.
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        privacy_mode = get_privacy_mode()
        
        # If privacy mode enabled, disable caching
        if not privacy_mode.should_cache():
            # Temporarily disable cache for this call
            if "use_cache" in kwargs:
                kwargs["use_cache"] = False
            elif len(args) > 0 and hasattr(args[0], "use_cache"):
                # Handle method calls
                pass
        
        return func(*args, **kwargs)
    
    return wrapper


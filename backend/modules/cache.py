"""
Caching module for LLM responses, search results, and embeddings.
Provides cost savings and performance improvements.
"""
import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import os

# Global registry for in-memory caches (used when privacy mode is enabled)
_in_memory_caches: Dict[str, Dict[str, Any]] = {}


class Cache:
    """
    Generic file-based cache with TTL support.
    """
    def __init__(self, cache_dir: str = "data/cache", default_ttl: int = 86400, in_memory: bool = False, cache_name: str = "default"):
        """
        Initialize cache.
        
        Args:
            cache_dir: Directory to store cache files (ignored if in_memory=True)
            default_ttl: Default time-to-live in seconds (default: 24 hours)
            in_memory: If True, store in RAM only (no disk writes). Used for privacy mode.
            cache_name: Name for this cache instance (used for in-memory registry)
        """
        self.in_memory = in_memory
        self.cache_name = cache_name
        
        if not in_memory:
            # Disk-based storage
            self.cache_dir = Path(cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            # In-memory storage (no disk paths)
            self.cache_dir = None
            # Register in global registry
            _in_memory_caches[cache_name] = {}
        
        self.default_ttl = default_ttl
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0
        }
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        if self.in_memory:
            raise ValueError("Cannot get cache path for in-memory cache")
        # Use hash of key to avoid long filenames
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        if self.in_memory:
            # In-memory cache lookup
            if self.cache_name not in _in_memory_caches:
                self.stats["misses"] += 1
                return None
            
            cache_data = _in_memory_caches[self.cache_name].get(key)
            if cache_data is None:
                self.stats["misses"] += 1
                return None
            
            # Check expiration
            expires_at = cache_data.get("expires_at")
            if expires_at and time.time() > expires_at:
                # Cache expired, remove it
                del _in_memory_caches[self.cache_name][key]
                self.stats["misses"] += 1
                self.stats["evictions"] += 1
                return None
            
            self.stats["hits"] += 1
            return cache_data.get("value")
        
        # Disk-based cache lookup
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            self.stats["misses"] += 1
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check expiration
            expires_at = data.get("expires_at")
            if expires_at and time.time() > expires_at:
                # Cache expired, remove it
                cache_path.unlink()
                self.stats["misses"] += 1
                self.stats["evictions"] += 1
                return None
            
            self.stats["hits"] += 1
            return data.get("value")
        
        except Exception as e:
            print(f"[cache] Error reading cache {key}: {e}")
            self.stats["misses"] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (uses default_ttl if None)
        
        Returns:
            True if successful
        """
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        
        try:
            data = {
                "key": key,
                "value": value,
                "created_at": time.time(),
                "expires_at": expires_at,
                "ttl": ttl
            }
            
            if self.in_memory:
                # In-memory cache storage
                if self.cache_name not in _in_memory_caches:
                    _in_memory_caches[self.cache_name] = {}
                _in_memory_caches[self.cache_name][key] = data
            else:
                # Disk-based cache storage
                cache_path = self._get_cache_path(key)
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.stats["sets"] += 1
            return True
        
        except Exception as e:
            print(f"[cache] Error writing cache {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        if self.in_memory:
            if self.cache_name in _in_memory_caches and key in _in_memory_caches[self.cache_name]:
                del _in_memory_caches[self.cache_name][key]
                return True
            return False
        else:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()
                return True
            return False
    
    def clear(self) -> int:
        """Clear all cache entries. Returns number of entries deleted."""
        if self.in_memory:
            if self.cache_name in _in_memory_caches:
                count = len(_in_memory_caches[self.cache_name])
                _in_memory_caches[self.cache_name].clear()
            else:
                count = 0
        else:
            count = 0
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                    count += 1
                except Exception as e:
                    print(f"[cache] Error deleting {cache_file}: {e}")
        
        self.stats["hits"] = 0
        self.stats["misses"] = 0
        self.stats["sets"] = 0
        self.stats["evictions"] = 0
        
        return count
    
    def cleanup_expired(self) -> int:
        """Remove expired cache entries. Returns number removed."""
        count = 0
        current_time = time.time()
        
        if self.in_memory:
            if self.cache_name in _in_memory_caches:
                keys_to_remove = []
                for key, data in _in_memory_caches[self.cache_name].items():
                    expires_at = data.get("expires_at")
                    if expires_at and current_time > expires_at:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del _in_memory_caches[self.cache_name][key]
                    count += 1
                    self.stats["evictions"] += 1
        else:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    expires_at = data.get("expires_at")
                    if expires_at and current_time > expires_at:
                        cache_file.unlink()
                        count += 1
                        self.stats["evictions"] += 1
                
                except Exception as e:
                    # Invalid cache file, remove it
                    print(f"[cache] Invalid cache file {cache_file}: {e}")
                    cache_file.unlink()
                    count += 1
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self.in_memory:
            if self.cache_name in _in_memory_caches:
                total_entries = len(_in_memory_caches[self.cache_name])
                # Estimate size (rough calculation)
                total_size = sum(len(json.dumps(v).encode()) for v in _in_memory_caches[self.cache_name].values())
            else:
                total_entries = 0
                total_size = 0
        else:
            total_entries = len(list(self.cache_dir.glob("*.json")))
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
        
        hit_rate = 0.0
        if self.stats["hits"] + self.stats["misses"] > 0:
            hit_rate = self.stats["hits"] / (self.stats["hits"] + self.stats["misses"])
        
        return {
            "total_entries": total_entries,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "evictions": self.stats["evictions"],
            "hit_rate": round(hit_rate * 100, 2),  # Percentage
            "storage_type": "in-memory" if self.in_memory else "disk"
        }


class LLMResponseCache:
    """
    Cache for LLM responses.
    Uses prompt + context hash as cache key.
    """
    def __init__(self, cache_dir: str = "data/cache/llm", ttl: int = 86400, in_memory: bool = False):
        """
        Initialize LLM response cache.
        
        Args:
            cache_dir: Cache directory (ignored if in_memory=True)
            ttl: Time-to-live in seconds (default: 24 hours)
            in_memory: If True, use in-memory storage (RAM only)
        """
        self.cache = Cache(cache_dir, default_ttl=ttl, in_memory=in_memory, cache_name="llm")
    
    def _generate_key(self, prompt: str, model: str, temperature: float = None, **kwargs) -> str:
        """
        Generate cache key from prompt and parameters.
        
        Args:
            prompt: LLM prompt
            model: Model name
            temperature: Temperature parameter (if applicable)
            **kwargs: Other parameters to include in key
        
        Returns:
            Cache key (hash)
        """
        # Create key from all relevant parameters
        key_data = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            **{k: v for k, v in kwargs.items() if k in ["max_tokens", "system"]}  # Include specific params
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return f"llm:{hashlib.sha256(key_string.encode()).hexdigest()}"
    
    def get(self, prompt: str, model: str, temperature: float = None, **kwargs) -> Optional[str]:
        """
        Get cached LLM response.
        
        Args:
            prompt: LLM prompt
            model: Model name
            temperature: Temperature parameter
            **kwargs: Other parameters
        
        Returns:
            Cached response or None
        """
        key = self._generate_key(prompt, model, temperature, **kwargs)
        return self.cache.get(key)
    
    def set(self, prompt: str, model: str, response: str, temperature: float = None, ttl: Optional[int] = None, **kwargs) -> bool:
        """
        Cache LLM response.
        
        Args:
            prompt: LLM prompt
            model: Model name
            response: LLM response
            temperature: Temperature parameter
            ttl: Time-to-live in seconds (optional)
            **kwargs: Other parameters
        
        Returns:
            True if successful
        """
        key = self._generate_key(prompt, model, temperature, **kwargs)
        return self.cache.set(key, response, ttl=ttl)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()


class SearchResultCache:
    """
    Cache for search results (vector + ripgrep).
    """
    def __init__(self, cache_dir: str = "data/cache/search", ttl: int = 3600, in_memory: bool = False):
        """
        Initialize search result cache.
        
        Args:
            cache_dir: Cache directory (ignored if in_memory=True)
            ttl: Time-to-live in seconds (default: 1 hour)
            in_memory: If True, use in-memory storage (RAM only)
        """
        self.cache = Cache(cache_dir, default_ttl=ttl, in_memory=in_memory, cache_name="search")
    
    def _generate_key(self, query: str, repo_dir: str, search_type: str = "hybrid") -> str:
        """
        Generate cache key from query and repo.
        
        Args:
            query: Search query
            repo_dir: Repository directory
            search_type: Type of search (hybrid, vector, keyword)
        
        Returns:
            Cache key
        """
        key_string = f"{search_type}:{repo_dir}:{query}"
        return f"search:{hashlib.sha256(key_string.encode()).hexdigest()}"
    
    def get(self, query: str, repo_dir: str, search_type: str = "hybrid") -> Optional[List[Dict]]:
        """Get cached search results."""
        key = self._generate_key(query, repo_dir, search_type)
        return self.cache.get(key)
    
    def set(self, query: str, repo_dir: str, results: List[Dict], search_type: str = "hybrid", ttl: Optional[int] = None) -> bool:
        """Cache search results."""
        key = self._generate_key(query, repo_dir, search_type)
        return self.cache.set(key, results, ttl=ttl)
    
    def invalidate_repo(self, repo_dir: str) -> int:
        """
        Invalidate all cache entries for a repository.
        Called when repository is re-indexed.
        
        Returns:
            Number of entries invalidated
        """
        # Note: This is a simple implementation
        # In production, you might want to store repo_dir in metadata
        # For now, we'll invalidate all search caches on repo change
        # (Could be optimized with better key structure)
        return 0  # TODO: Implement repo-specific invalidation
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()


class EmbeddingCache:
    """
    Cache for file embeddings.
    Uses file hash + modification time as cache key.
    """
    def __init__(self, cache_dir: str = "data/cache/embeddings", ttl: int = 604800, in_memory: bool = False):
        """
        Initialize embedding cache.
        
        Args:
            cache_dir: Cache directory (ignored if in_memory=True)
            ttl: Time-to-live in seconds (default: 7 days)
            in_memory: If True, use in-memory storage (RAM only)
        """
        self.cache = Cache(cache_dir, default_ttl=ttl, in_memory=in_memory, cache_name="embeddings")
    
    def _generate_key(self, file_path: str, model_name: str) -> str:
        """
        Generate cache key from file path and model.
        
        Args:
            file_path: Path to file
            model_name: Embedding model name
        
        Returns:
            Cache key
        """
        file_path_obj = Path(file_path)
        
        # Get file hash and modification time
        if file_path_obj.exists():
            stat = file_path_obj.stat()
            file_hash = hashlib.md5(f"{file_path}:{stat.st_mtime}:{stat.st_size}".encode()).hexdigest()
        else:
            file_hash = hashlib.md5(file_path.encode()).hexdigest()
        
        return f"embedding:{model_name}:{file_hash}"
    
    def get(self, file_path: str, model_name: str) -> Optional[List[float]]:
        """Get cached embedding for file."""
        key = self._generate_key(file_path, model_name)
        return self.cache.get(key)
    
    def set(self, file_path: str, model_name: str, embedding: List[float], ttl: Optional[int] = None) -> bool:
        """Cache file embedding."""
        key = self._generate_key(file_path, model_name)
        return self.cache.set(key, embedding, ttl=ttl)
    
    def invalidate_file(self, file_path: str, model_name: str = None) -> int:
        """
        Invalidate cache for a specific file.
        Called when file is modified.
        
        Args:
            file_path: Path to file
            model_name: Model name (optional, invalidates all models if None)
        
        Returns:
            Number of entries invalidated
        """
        count = 0
        
        if model_name:
            # Invalidate specific model
            key = self._generate_key(file_path, model_name)
            if self.cache.delete(key):
                count += 1
        else:
            # Invalidate all models for this file
            # This requires checking all cache files (can be optimized)
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                stat = file_path_obj.stat()
                file_hash = hashlib.md5(f"{file_path}:{stat.st_mtime}:{stat.st_size}".encode()).hexdigest()
            else:
                file_hash = hashlib.md5(file_path.encode()).hexdigest()
            
            # Delete all cache files matching this file hash
            pattern = f"*{file_hash[:16]}*.json"  # Use first 16 chars for pattern matching
            for cache_file in self.cache.cache_dir.glob(pattern):
                cache_file.unlink()
                count += 1
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()


# Global cache instances (singletons)
_llm_cache: Optional[LLMResponseCache] = None
_search_cache: Optional[SearchResultCache] = None
_embedding_cache: Optional[EmbeddingCache] = None


def get_llm_cache(cache_dir: str = "data/cache/llm", ttl: int = 86400, in_memory: bool = None) -> LLMResponseCache:
    """
    Get or create LLM response cache singleton.
    
    Args:
        cache_dir: Cache directory (ignored if in_memory=True)
        ttl: Time-to-live in seconds
        in_memory: If True, use in-memory storage. If None, auto-detect from privacy mode.
    """
    global _llm_cache
    if in_memory is None:
        # Auto-detect from privacy mode
        from backend.modules.privacy import get_privacy_mode
        in_memory = get_privacy_mode().use_in_memory_storage()
    
    if _llm_cache is None:
        _llm_cache = LLMResponseCache(cache_dir, ttl, in_memory=in_memory)
    return _llm_cache


def get_search_cache(cache_dir: str = "data/cache/search", ttl: int = 3600, in_memory: bool = None) -> SearchResultCache:
    """
    Get or create search result cache singleton.
    
    Args:
        cache_dir: Cache directory (ignored if in_memory=True)
        ttl: Time-to-live in seconds
        in_memory: If True, use in-memory storage. If None, auto-detect from privacy mode.
    """
    global _search_cache
    if in_memory is None:
        # Auto-detect from privacy mode
        from backend.modules.privacy import get_privacy_mode
        in_memory = get_privacy_mode().use_in_memory_storage()
    
    if _search_cache is None:
        _search_cache = SearchResultCache(cache_dir, ttl, in_memory=in_memory)
    return _search_cache


def get_embedding_cache(cache_dir: str = "data/cache/embeddings", ttl: int = 604800, in_memory: bool = None) -> EmbeddingCache:
    """
    Get or create embedding cache singleton.
    
    Args:
        cache_dir: Cache directory (ignored if in_memory=True)
        ttl: Time-to-live in seconds
        in_memory: If True, use in-memory storage. If None, auto-detect from privacy mode.
    """
    global _embedding_cache
    if in_memory is None:
        # Auto-detect from privacy mode
        from backend.modules.privacy import get_privacy_mode
        in_memory = get_privacy_mode().use_in_memory_storage()
    
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache(cache_dir, ttl, in_memory=in_memory)
    return _embedding_cache


def get_all_cache_stats() -> Dict[str, Any]:
    """Get statistics from all caches."""
    return {
        "llm": get_llm_cache().get_stats(),
        "search": get_search_cache().get_stats(),
        "embeddings": get_embedding_cache().get_stats()
    }


def clear_all_caches() -> Dict[str, int]:
    """Clear all caches. Returns count of entries cleared per cache."""
    return {
        "llm": get_llm_cache().cache.clear(),
        "search": get_search_cache().cache.clear(),
        "embeddings": get_embedding_cache().cache.clear()
    }


def cleanup_all_caches() -> Dict[str, int]:
    """Remove expired entries from all caches."""
    return {
        "llm": get_llm_cache().cache.cleanup_expired(),
        "search": get_search_cache().cache.cleanup_expired(),
        "embeddings": get_embedding_cache().cache.cleanup_expired()
    }


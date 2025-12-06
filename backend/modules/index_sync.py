"""
Index synchronization manager for automatic index updates.
Manages file watchers and incremental indexing.
"""
import threading
from pathlib import Path
from typing import Dict, Set, Optional
from backend.modules.file_watcher import RepoWatcher, WATCHDOG_AVAILABLE
from backend.modules.vector_store import FaissStore
from backend.modules.parser import semantic_chunks, fallback_line_chunks, iter_text_files, should_ignore, load_gitignore
from backend.config import DATA_DIR


class IndexSyncManager:
    """Manages automatic index synchronization for repositories."""
    
    def __init__(self):
        self.watchers: Dict[str, RepoWatcher] = {}
        self.lock = threading.Lock()
        self.enabled = True
    
    def watch_repo(self, repo_dir: str, repo_id: str, base_dir: str = None):
        """
        Start watching a repository for changes.
        
        Args:
            repo_dir: Repository directory path
            repo_id: Repository ID (for index path)
            base_dir: Base directory for indices (defaults to DATA_DIR/index)
        """
        if not WATCHDOG_AVAILABLE:
            print("[index_sync] watchdog not available. Install with: pip install watchdog")
            return
        
        if not self.enabled:
            return
        
        repo_path = Path(repo_dir).resolve()
        
        with self.lock:
            if repo_id in self.watchers:
                # Already watching
                return
            
            # Load ignore patterns
            ignore_patterns = load_gitignore(repo_path)
            
            # Create callback
            def on_file_change(file_path: str, event_type: str):
                self._handle_file_change(repo_dir, repo_id, file_path, event_type, base_dir)
            
            # Create and start watcher
            try:
                watcher = RepoWatcher(str(repo_path), on_file_change, ignore_patterns)
                watcher.start()
                self.watchers[repo_id] = watcher
                print(f"[index_sync] Started watching repository: {repo_id} ({repo_dir})")
            except Exception as e:
                print(f"[index_sync] Error starting watcher for {repo_id}: {e}")
    
    def unwatch_repo(self, repo_id: str):
        """Stop watching a repository."""
        with self.lock:
            if repo_id in self.watchers:
                watcher = self.watchers.pop(repo_id)
                watcher.stop()
                print(f"[index_sync] Stopped watching repository: {repo_id}")
    
    def _handle_file_change(self, repo_dir: str, repo_id: str, file_path: str, event_type: str, base_dir: Optional[str] = None):
        """Handle file change event."""
        repo_path = Path(repo_dir).resolve()
        file_path_obj = Path(file_path).resolve()
        
        # Make path relative to repo
        try:
            relative_path = file_path_obj.relative_to(repo_path)
        except ValueError:
            # File not in repo (shouldn't happen)
            return
        
        # Check if should ignore
        ignore_patterns = load_gitignore(repo_path)
        if should_ignore(file_path_obj, repo_path, ignore_patterns):
            return
        
        print(f"[index_sync] File {event_type}: {relative_path}")
        
        # Get store
        if base_dir is None:
            base_dir = f"{DATA_DIR}/index"
        
        store = FaissStore(repo_id, base_dir=base_dir)
        
        # Check if index exists
        if not store.index_path.exists():
            print(f"[index_sync] Index not found for {repo_id}, skipping update")
            return
        
        try:
            store.load()
        except Exception as e:
            print(f"[index_sync] Error loading index for {repo_id}: {e}")
            return
        
        # Handle different event types
        if event_type in ['created', 'modified']:
            # Add/update file chunks
            if file_path_obj.exists() and file_path_obj.is_file():
                try:
                    # Get chunks for this file
                    chunks = semantic_chunks(file_path_obj)
                    if not chunks:
                        chunks = fallback_line_chunks(file_path_obj)
                    
                    # Update in index
                    store.update_file_chunks(str(file_path_obj), chunks)
                    print(f"[index_sync] Updated index for {relative_path} ({len(chunks)} chunks)")
                except Exception as e:
                    print(f"[index_sync] Error updating {relative_path}: {e}")
        
        elif event_type == 'deleted':
            # Remove file chunks
            try:
                store.remove_chunks_by_file(str(file_path_obj))
                print(f"[index_sync] Removed {relative_path} from index")
            except Exception as e:
                print(f"[index_sync] Error removing {relative_path}: {e}")
        
        # Save store
        try:
            import faiss
            faiss.write_index(store.index, str(store.index_path))
            with open(store.meta_path, "w", encoding="utf-8") as f:
                import json
                json.dump(store.metas, f, ensure_ascii=False)
        except Exception as e:
            print(f"[index_sync] Error saving index: {e}")
    
    def stop_all(self):
        """Stop all watchers."""
        with self.lock:
            for repo_id in list(self.watchers.keys()):
                self.unwatch_repo(repo_id)
    
    def is_watching(self, repo_id: str) -> bool:
        """Check if a repository is being watched."""
        return repo_id in self.watchers


# Global manager instance
_sync_manager: Optional[IndexSyncManager] = None


def get_sync_manager() -> IndexSyncManager:
    """Get global index sync manager instance."""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = IndexSyncManager()
    return _sync_manager


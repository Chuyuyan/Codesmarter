"""
File watcher for automatic index updates when code changes.
Uses watchdog library to monitor file system changes.
"""
import time
import threading
from pathlib import Path
from typing import Dict, Set, Callable, Optional
from queue import Queue
import fnmatch

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # Dummy classes for when watchdog is not available
    class FileSystemEventHandler:
        pass
    class FileSystemEvent:
        pass
    Observer = None
    print("[file_watcher] watchdog not installed. Run: pip install watchdog")


if WATCHDOG_AVAILABLE:
    class CodeChangeHandler(FileSystemEventHandler):
        """Handles file system events for code files."""
        
        def __init__(self, callback: Callable[[str, str], None], ignore_patterns: Set[str]):
            """
            Args:
                callback: Function to call with (file_path, event_type)
                ignore_patterns: Patterns to ignore (from .gitignore and config)
            """
            self.callback = callback
            self.ignore_patterns = ignore_patterns
            self.event_queue = Queue()
            self.debounce_time = 2.0  # Wait 2 seconds after last change
            self.last_event_time = {}
            self.processing_thread = None
            self._stop_processing = False
        
        def should_ignore(self, file_path: str) -> bool:
            """Check if file should be ignored based on patterns."""
            path_obj = Path(file_path)
            
            # Check each pattern
            for pattern in self.ignore_patterns:
                # Convert pattern to work with fnmatch
                if pattern.endswith('/'):
                    # Directory pattern - only match if actual directory in path
                    pattern_str = pattern.rstrip('/')
                    # Check if any parent directory name matches (not file name)
                    for parent in path_obj.parents:
                        if fnmatch.fnmatch(parent.name, pattern_str) or pattern_str in str(parent):
                            return True
                    # Don't match file names with directory patterns
                else:
                    # File pattern - match filename or full path
                    if fnmatch.fnmatch(path_obj.name, pattern) or fnmatch.fnmatch(str(path_obj), pattern):
                        return True
                    # Check parent directories (for patterns like "test_*")
                    for parent in path_obj.parents:
                        if fnmatch.fnmatch(parent.name, pattern):
                            return True
            
            # Also check file extension - we only care about code files
            code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', 
                              '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
                              '.vue', '.svelte', '.html', '.css', '.scss', '.less'}
            
            # Check if it's a code file (has code extension or is in typical code directories)
            has_code_ext = any(path_obj.suffix.lower() in code_extensions for _ in [1])
            
            # Ignore if it's not a code file and not in typical code directories
            if not has_code_ext and path_obj.suffix.lower() not in {'.json', '.md', '.txt', '.yml', '.yaml'}:
                # Could be a binary or other file
                if path_obj.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.exe'}:
                    return True
            
            return False
        
        def on_modified(self, event: FileSystemEvent):
            if event.is_directory:
                return
            self._handle_event(event.src_path, 'modified')
        
        def on_created(self, event: FileSystemEvent):
            if event.is_directory:
                return
            self._handle_event(event.src_path, 'created')
        
        def on_deleted(self, event: FileSystemEvent):
            if event.is_directory:
                return
            self._handle_event(event.src_path, 'deleted')
        
        def on_moved(self, event: FileSystemEvent):
            if event.is_directory:
                return
            # Handle move as delete + create
            if hasattr(event, 'dest_path'):
                self._handle_event(event.src_path, 'deleted')
                self._handle_event(event.dest_path, 'created')
            else:
                self._handle_event(event.src_path, 'deleted')
        
        def _handle_event(self, file_path: str, event_type: str):
            """Handle file system event with debouncing."""
            # Normalize path
            file_path = str(Path(file_path).resolve())
            
            # Check if should ignore
            if self.should_ignore(file_path):
                print(f"[file_watcher] Ignored event: {event_type} - {Path(file_path).name}")
                return
            
            print(f"[file_watcher] Event detected: {event_type} - {Path(file_path).name}")

            # Debounce: only process if no event for this file in last N seconds
            current_time = time.time()
            last_time = self.last_event_time.get(file_path, 0)
            
            if current_time - last_time < self.debounce_time:
                # Update timestamp, but don't process yet
                self.last_event_time[file_path] = current_time
                print(f"[file_watcher] Debouncing event for: {Path(file_path).name}")
                return
            
            # Add to queue
            self.event_queue.put((file_path, event_type, current_time))
            self.last_event_time[file_path] = current_time
            print(f"[file_watcher] Queuing event: {event_type} - {Path(file_path).name}")
            
            # Start processing thread if not running
            if self.processing_thread is None or not self.processing_thread.is_alive():
                print(f"[file_watcher] Starting event processing thread")
                self.processing_thread = threading.Thread(target=self._process_events, daemon=True)
                self.processing_thread.start()
        
        def _process_events(self):
            """Process events from queue with debouncing."""
            pending_events = {}
            
            while not self._stop_processing:
                try:
                    # Get event with timeout
                    event = self.event_queue.get(timeout=1.0)
                    file_path, event_type, event_time = event
                    
                    # Group events by file
                    pending_events[file_path] = (event_type, event_time)
                    
                    # Wait for debounce period
                    time.sleep(self.debounce_time)
                    
                    # Process all pending events
                    for path, (evt_type, evt_time) in list(pending_events.items()):
                        # Check if still recent (no new events)
                        if time.time() - evt_time >= self.debounce_time:
                            try:
                                print(f"[file_watcher] Processing event: {evt_type} - {Path(path).name}")
                                self.callback(path, evt_type)
                            except Exception as e:
                                print(f"[file_watcher] Error processing {path}: {e}")
                            del pending_events[path]
                    
                except:  # Empty queue or timeout
                    # Process pending if any
                    current_time = time.time()
                    for path in list(pending_events.keys()):
                        evt_type, evt_time = pending_events[path]
                        if current_time - evt_time >= self.debounce_time:
                            try:
                                self.callback(path, evt_type)
                            except Exception as e:
                                print(f"[file_watcher] Error processing {path}: {e}")
                            del pending_events[path]
        
        def stop(self):
            """Stop processing events."""
            self._stop_processing = True
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=self.debounce_time + 1)  # Give it time to finish
            print("[file_watcher] Event processing thread stopped.")
else:
    # Dummy class when watchdog not available
    class CodeChangeHandler:
        pass


if WATCHDOG_AVAILABLE:
    class RepoWatcher:
        """Watches a repository directory for changes."""
        
        def __init__(self, repo_dir: str, callback: Callable[[str, str], None], ignore_patterns: Set[str]):
            """
            Args:
                repo_dir: Repository directory to watch
                callback: Function to call with (file_path, event_type) when file changes
                ignore_patterns: Patterns to ignore
            """
            if not WATCHDOG_AVAILABLE:
                raise ImportError("watchdog library not installed. Run: pip install watchdog")
            
            self.repo_dir = Path(repo_dir).resolve()
            self.callback = callback
            self.ignore_patterns = ignore_patterns
            self.observer = None
            self.handler = None
            self.is_watching = False
        
        def start(self):
            """Start watching the repository."""
            if self.is_watching:
                return
            
            self.handler = CodeChangeHandler(self.callback, self.ignore_patterns)
            self.observer = Observer()
            self.observer.schedule(self.handler, str(self.repo_dir), recursive=True)
            self.observer.start()
            self.is_watching = True
            print(f"[file_watcher] Started watching: {self.repo_dir}")
        
        def stop(self):
            """Stop watching the repository."""
            if not self.is_watching:
                return
            
            if self.handler:
                self.handler.stop()
            if self.observer:
                self.observer.stop()
                self.observer.join()
            
            self.is_watching = False
            print(f"[file_watcher] Stopped watching: {self.repo_dir}")


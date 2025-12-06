"""
Conversation history management for chat context.
Stores and retrieves conversation history to maintain context across messages.
"""
import json
import time
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime, timedelta
from backend.config import DATA_DIR


class ConversationMessage:
    """Represents a single message in a conversation."""
    def __init__(self, role: str, content: str, timestamp: float = None):
        """
        Args:
            role: "user" or "assistant"
            content: Message content
            timestamp: Unix timestamp (defaults to now)
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationMessage':
        """Create from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", time.time())
        )


class ConversationHistory:
    """
    Manages conversation history for a single conversation session.
    """
    def __init__(self, conversation_id: str, in_memory: bool = False):
        """
        Args:
            conversation_id: Unique identifier for the conversation
            in_memory: If True, store in RAM only (for privacy mode)
        """
        self.conversation_id = conversation_id
        self.in_memory = in_memory
        self.messages: List[ConversationMessage] = []
        self.created_at = time.time()
        self.last_updated = time.time()
        
        if not in_memory:
            # Disk-based storage
            self.history_dir = Path(DATA_DIR) / "conversations"
            self.history_dir.mkdir(parents=True, exist_ok=True)
            self.history_file = self.history_dir / f"{conversation_id}.json"
            self._load_from_disk()
    
    def _load_from_disk(self):
        """Load conversation history from disk."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.messages = [ConversationMessage.from_dict(msg) for msg in data.get("messages", [])]
                    self.created_at = data.get("created_at", time.time())
                    self.last_updated = data.get("last_updated", time.time())
            except Exception as e:
                print(f"[conversation_history] Error loading history: {e}")
                self.messages = []
    
    def _save_to_disk(self):
        """Save conversation history to disk."""
        if not self.in_memory:
            try:
                data = {
                    "conversation_id": self.conversation_id,
                    "created_at": self.created_at,
                    "last_updated": self.last_updated,
                    "messages": [msg.to_dict() for msg in self.messages]
                }
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[conversation_history] Error saving history: {e}")
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation."""
        message = ConversationMessage(role, content)
        self.messages.append(message)
        self.last_updated = time.time()
        self._save_to_disk()
    
    def get_messages(self, max_messages: Optional[int] = None) -> List[Dict]:
        """
        Get conversation messages.
        
        Args:
            max_messages: Maximum number of messages to return (most recent)
        
        Returns:
            List of message dictionaries
        """
        messages = self.messages
        if max_messages:
            messages = messages[-max_messages:]
        return [msg.to_dict() for msg in messages]
    
    def get_recent_messages(self, max_tokens: int = 2000) -> List[Dict]:
        """
        Get recent messages within token limit.
        Uses simple token estimation (1 token ≈ 4 characters).
        
        Args:
            max_tokens: Maximum tokens to include
        
        Returns:
            List of message dictionaries (most recent first, within token limit)
        """
        recent_messages = []
        total_tokens = 0
        
        # Start from most recent and work backwards
        for message in reversed(self.messages):
            # Simple token estimation: 1 token ≈ 4 characters
            message_tokens = len(message.content) // 4
            if total_tokens + message_tokens > max_tokens:
                break
            recent_messages.insert(0, message.to_dict())
            total_tokens += message_tokens
        
        return recent_messages
    
    def clear(self):
        """Clear all messages from the conversation."""
        self.messages = []
        self.last_updated = time.time()
        if not self.in_memory and self.history_file.exists():
            self.history_file.unlink()
        else:
            self._save_to_disk()
    
    def get_summary(self) -> Dict:
        """Get conversation summary."""
        return {
            "conversation_id": self.conversation_id,
            "message_count": len(self.messages),
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "in_memory": self.in_memory
        }


# Global conversation store (in-memory for privacy mode, disk for normal)
_conversations: Dict[str, ConversationHistory] = {}


def get_conversation(conversation_id: str, in_memory: bool = False) -> ConversationHistory:
    """
    Get or create a conversation history.
    
    Args:
        conversation_id: Unique identifier for the conversation
        in_memory: If True, store in RAM only (for privacy mode)
    
    Returns:
        ConversationHistory instance
    """
    if conversation_id not in _conversations:
        _conversations[conversation_id] = ConversationHistory(conversation_id, in_memory=in_memory)
    return _conversations[conversation_id]


def clear_conversation(conversation_id: str):
    """Clear a conversation history."""
    if conversation_id in _conversations:
        _conversations[conversation_id].clear()
        del _conversations[conversation_id]


def clear_all_conversations():
    """Clear all conversation histories."""
    for conv_id in list(_conversations.keys()):
        clear_conversation(conv_id)


def cleanup_old_conversations(max_age_hours: int = 24):
    """
    Clean up old conversations.
    
    Args:
        max_age_hours: Maximum age in hours before cleanup
    """
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    to_remove = []
    for conv_id, conv in _conversations.items():
        age = current_time - conv.last_updated
        if age > max_age_seconds:
            to_remove.append(conv_id)
    
    for conv_id in to_remove:
        clear_conversation(conv_id)
        print(f"[conversation_history] Cleaned up old conversation: {conv_id}")


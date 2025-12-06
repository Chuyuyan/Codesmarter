# Conversation History Feature

## 🎯 Overview

The chat endpoint now supports **conversation history**, allowing the AI to remember previous messages and maintain context across multiple interactions. This makes conversations more natural and context-aware, just like talking to a colleague!

## ✨ Features

1. **Conversation Memory**: Remembers previous messages in a conversation
2. **Context-Aware Responses**: AI understands what was discussed before
3. **Token-Aware History**: Automatically manages history within token limits
4. **Privacy Mode Support**: Uses in-memory storage when privacy mode is enabled
5. **Automatic Management**: History is saved and loaded automatically

## 📝 How It Works

### **Basic Usage (No History)**

```python
POST /chat {
  "question": "How does authentication work?",
  "repo_dir": "/path/to/repo"
}
```

**Result:** Single question, no context from previous messages.

---

### **With Conversation History**

```python
# First message
POST /chat {
  "question": "How does authentication work?",
  "repo_dir": "/path/to/repo",
  "conversation_id": "user-123"  // Start a conversation
}

# Second message (remembers first message)
POST /chat {
  "question": "Can you show me where the JWT token is validated?",
  "repo_dir": "/path/to/repo",
  "conversation_id": "user-123"  // Same conversation ID
}

# AI remembers: "You asked about authentication, now you want to see JWT validation"
```

---

## 🔧 API Parameters

### **conversation_id** (Optional)
- **Type**: String
- **Description**: Unique identifier for the conversation
- **Example**: `"user-123"`, `"session-abc"`, `"chat-xyz"`
- **Usage**: Use the same ID across multiple messages to maintain context

### **clear_history** (Optional)
- **Type**: Boolean
- **Default**: `false`
- **Description**: Clear all previous messages in the conversation
- **Usage**: Set to `true` to start fresh while keeping the same conversation_id

---

## 💡 Examples

### **Example 1: Multi-Turn Conversation**

```python
# Message 1
POST /chat {
  "question": "What is the main entry point of this application?",
  "repo_dir": "/my/project",
  "conversation_id": "session-1"
}

# Response: "The main entry point is app.py, which initializes the Flask server..."

# Message 2 (remembers Message 1)
POST /chat {
  "question": "How does it handle routing?",
  "repo_dir": "/my/project",
  "conversation_id": "session-1"
}

# Response: "Based on the app.py we discussed, routing is handled by Flask's @app.route decorators..."
# ✅ AI remembers we were talking about app.py!
```

### **Example 2: Follow-up Questions**

```python
# Message 1
POST /chat {
  "question": "Explain the authentication system",
  "repo_dir": "/my/project",
  "conversation_id": "auth-discussion"
}

# Message 2
POST /chat {
  "question": "What about the refresh token mechanism?",
  "repo_dir": "/my/project",
  "conversation_id": "auth-discussion"
}

# ✅ AI knows "refresh token" is related to "authentication system" we just discussed
```

### **Example 3: Clear History**

```python
# Message 1
POST /chat {
  "question": "How does authentication work?",
  "conversation_id": "session-1"
}

# Message 2: Clear history and start fresh
POST /chat {
  "question": "How does the database work?",
  "conversation_id": "session-1",
  "clear_history": true  // Start fresh
}

# ✅ Previous authentication discussion is cleared
```

---

## 🗄️ Storage

### **Normal Mode (Disk Storage)**
- Conversations stored in: `data/conversations/{conversation_id}.json`
- Persists across server restarts
- Can be manually deleted

### **Privacy Mode (In-Memory Storage)**
- Conversations stored in RAM only
- Cleared on server shutdown
- No disk files created

---

## 📊 Token Management

The system automatically manages conversation history to stay within token limits:

- **Max History Tokens**: 2000 tokens (configurable)
- **Token Estimation**: 1 token ≈ 4 characters
- **Recent Messages First**: Most recent messages are kept
- **Automatic Truncation**: Older messages are removed if needed

**Example:**
```
Conversation has 10 messages (5000 tokens)
System keeps: Last 4 messages (2000 tokens)
Result: AI sees recent context, stays within limits
```

---

## 🎯 Benefits

1. **Natural Conversations**
   - Ask follow-up questions
   - Reference previous topics
   - More human-like interaction

2. **Context Awareness**
   - AI understands what you discussed
   - No need to repeat context
   - Better answers

3. **Efficient**
   - Token-aware management
   - Automatic cleanup
   - Privacy mode support

---

## 🔍 Technical Details

### **How History is Used**

1. **User sends message** with `conversation_id`
2. **System loads** previous messages from history
3. **LLM receives** conversation history + current question
4. **LLM responds** with context awareness
5. **System saves** user message + AI response to history

### **Message Format**

```json
{
  "role": "user" | "assistant",
  "content": "Message text",
  "timestamp": 1234567890.123
}
```

### **LLM Prompt Structure**

```
[Previous Messages]
User: "How does auth work?"
Assistant: "Authentication uses JWT tokens..."

[Current Question with Code Context]
User: "Where is the token validated?"
[Code Evidence...]
```

---

## ⚠️ Limitations

1. **Token Limits**: History is truncated to stay within limits
2. **No Cross-Conversation Memory**: Each `conversation_id` is independent
3. **Server Restart**: In-memory conversations are lost (privacy mode)
4. **No Automatic Cleanup**: Old conversations persist (disk mode)

---

## 🚀 Best Practices

1. **Use Unique IDs**: Use unique `conversation_id` per user/session
2. **Clear When Needed**: Use `clear_history=true` to start fresh
3. **Monitor Token Usage**: Long conversations may truncate history
4. **Privacy Mode**: Use in-memory storage for sensitive conversations

---

## 📝 Example Workflow

```python
# Start a conversation
conversation_id = "user-123"

# Question 1
POST /chat {
  "question": "What is this codebase about?",
  "conversation_id": conversation_id
}
# AI: "This is a Flask web application..."

# Question 2 (remembers Question 1)
POST /chat {
  "question": "How does it handle user authentication?",
  "conversation_id": conversation_id
}
# AI: "Based on the Flask app we discussed, authentication uses..."

# Question 3 (remembers Questions 1 & 2)
POST /chat {
  "question": "Show me the login endpoint",
  "conversation_id": conversation_id
}
# AI: "In the authentication system we discussed, the login endpoint is..."
```

---

## ✅ Summary

**Conversation history makes the chat:**
- ✅ More natural and conversational
- ✅ Context-aware and intelligent
- ✅ Efficient with token management
- ✅ Privacy-friendly (in-memory option)

**Just add `conversation_id` to your requests and the AI will remember!** 🎉


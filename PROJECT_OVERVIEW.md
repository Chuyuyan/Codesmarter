# Code Analysis Assistant - Complete Project Overview

A Cursor-like AI-powered code analysis system that understands, searches, and analyzes your codebase using semantic search and Large Language Models.

---

## 🎯 What is This Project?

This is a **comprehensive code analysis system** similar to Cursor IDE. It allows you to:
- **Index** your codebase for fast semantic search
- **Ask questions** about your code in natural language
- **Get AI-powered answers** with code citations
- **Refactor code** with before/after examples
- **Automatically sync** changes to keep the index up-to-date

Think of it as having an AI pair programmer that understands your entire codebase!

---

## ✨ Core Features

### 1. **Repository Indexing** 📚
- **Semantic chunking**: Breaks code into logical units (functions, classes) using tree-sitter
- **Vector embeddings**: Uses sentence transformers to convert code into searchable vectors
- **FAISS index**: Fast similarity search using Facebook's FAISS library
- **Smart filtering**: Automatically excludes `node_modules`, `.git`, build artifacts, etc.
- **Gitignore support**: Respects your `.gitignore` patterns

**How it works:**
1. Scans repository for code files
2. Splits code into semantic chunks (functions, classes)
3. Converts chunks to vector embeddings
4. Builds searchable FAISS index
5. Stores metadata for citations

### 2. **Hybrid Code Search** 🔍
- **Vector search**: Semantic similarity using embeddings
- **Keyword search**: Fast text search using ripgrep
- **Fused results**: Combines both approaches for best results
- **Context expansion**: Automatically includes related code (imports, function boundaries)

**Search capabilities:**
- Find functions by what they do (semantic)
- Find code by keywords (text search)
- Get surrounding context automatically

### 3. **AI-Powered Chat Interface** 💬
- **Natural language queries**: Ask questions in plain English
- **Code explanations**: Understand what code does
- **Multiple analysis types**:
  - **Explain**: Understand code functionality
  - **Refactor**: Get improvement suggestions
  - **Debug**: Find potential issues
  - **Optimize**: Performance improvements
- **Streaming responses**: Real-time answer generation (like ChatGPT)
- **Code citations**: See exactly where answers come from

**Example queries:**
- "How does authentication work in this codebase?"
- "What's the main structure of this project?"
- "Explain this function in detail"

### 4. **Dedicated Refactoring Endpoint** 🔧
- **Before/after examples**: See exactly how to improve code
- **Three input modes**:
  - **Query mode**: Search for code to refactor
  - **File mode**: Refactor entire files
  - **Snippet mode**: Provide code directly
- **Focus areas**: Performance, readability, maintainability, design patterns
- **Detailed suggestions**: Multiple refactoring options with explanations

**Refactoring features:**
- Extract constants and configuration
- Component extraction suggestions
- Type safety improvements
- Code structure recommendations

### 5. **Automatic Code Change Tracking** 🔄
- **File watching**: Monitors repository for changes using `watchdog`
- **Auto-sync**: Automatically updates index when files change
- **Debouncing**: Waits for file edits to complete before processing
- **Incremental updates**: Only updates changed files, not entire index
- **Event handling**: Detects file creation, modification, deletion

**How it works:**
1. Watchdog monitors file system events
2. Debounces rapid changes (2-second delay)
3. Updates FAISS index for changed files
4. Keeps index in sync without manual re-indexing

### 6. **Enhanced Code Context** 📖
- **Function boundary detection**: Includes complete functions/classes
- **Import statements**: Automatically includes relevant imports
- **Context expansion**: Adds surrounding code (10-15 lines)
- **Multi-language support**: Python, JavaScript, TypeScript, and more

### 7. **Web UI** 🌐
- **Modern interface**: Clean, responsive design
- **Chat interface**: Interactive Q&A with your codebase
- **Analysis type selector**: Choose explain, refactor, debug, optimize
- **Streaming support**: Real-time response generation
- **Code citation display**: See source files and line numbers

### 8. **VS Code Extension** 🎨
- **Integrated chat panel**: Ask questions directly in VS Code
- **Webview interface**: Beautiful chat UI within VS Code
- **Command palette**: Quick access to code assistant
- **Repository detection**: Automatically uses current workspace

---

## 🏗️ Technical Architecture

### Backend Stack
- **Flask**: RESTful API server
- **FAISS**: Vector similarity search
- **Sentence Transformers**: Code embeddings (all-MiniLM-L6-v2)
- **Tree-sitter**: Semantic code parsing (with regex fallback)
- **Ripgrep**: Fast text search
- **Watchdog**: File system monitoring
- **OpenAI-compatible APIs**: LLM integration (DeepSeek, OpenAI, Anthropic, Qwen)

### Frontend Stack
- **Vanilla JavaScript**: Simple, fast web interface
- **VS Code Extension**: TypeScript + VS Code API

### Data Storage
- **FAISS index**: Vector embeddings
- **JSON metadata**: Code snippets with file paths and line numbers
- **File system**: Indexed data stored in `data/index/`

---

## 📡 API Endpoints

### Core Endpoints

1. **`GET /health`**
   - Health check endpoint
   - Returns server status

2. **`POST /index_repo`**
   - Index a repository for analysis
   - Parameters: `repo_dir` (repository path)
   - Returns: `repo_id`, number of chunks indexed
   - Automatically starts file watching after indexing

3. **`POST /search`**
   - Hybrid search (vector + keyword)
   - Parameters: `repo_dir`, `query`, `k` (optional, default: 6)
   - Returns: Relevant code snippets with scores

4. **`POST /chat`**
   - Main chat endpoint (unified Q&A)
   - Parameters:
     - `repo_dir`: Repository path
     - `question`: Your question
     - `analysis_type`: "explain", "refactor", "debug", "optimize" (optional)
     - `stream`: Boolean for streaming response (optional)
     - `top_k`: Number of code snippets (optional)
   - Returns: Answer with citations and evidences

5. **`POST /refactor`**
   - Dedicated refactoring endpoint
   - Parameters:
     - `repo_dir`: Repository path (for query/file modes)
     - `query`: Search query (optional)
     - `file_path`: Specific file path (optional)
     - `code_snippets`: Direct code snippets (optional)
     - `focus`: "performance", "readability", "maintainability", etc. (optional)
     - `top_k`: Number of snippets to analyze (optional)
   - Returns: Refactoring suggestions with before/after examples

6. **`POST /answer`** (Legacy)
   - Legacy endpoint for backward compatibility
   - Parameters: `question`, `evidences`

### Static Files
- **`GET /`**: Web UI interface

---

## 🔧 Key Modules

### `backend/modules/parser.py`
- **Semantic chunking**: Uses tree-sitter for AST-based parsing
- **Fallback chunking**: Regex-based line chunking if tree-sitter unavailable
- **File filtering**: Ignores patterns from `.gitignore` and defaults
- **Multi-language support**: Python, JavaScript, TypeScript, and more

### `backend/modules/vector_store.py`
- **FAISS index management**: Build, load, save vector indexes
- **Incremental updates**: Add, remove, update chunks without rebuilding
- **Embedding generation**: Converts code to vectors using sentence transformers

### `backend/modules/search.py`
- **Ripgrep integration**: Fast keyword search
- **Result fusion**: Combines vector and keyword search results
- **Ranking**: Scores and sorts results by relevance

### `backend/modules/llm_api.py`
- **Multi-provider support**: DeepSeek, OpenAI, Anthropic, Qwen
- **Answer generation**: Creates answers with code citations
- **Streaming support**: Real-time response streaming
- **Refactoring suggestions**: Generates before/after examples

### `backend/modules/context_retriever.py`
- **Context expansion**: Adds surrounding code and imports
- **Boundary detection**: Finds function/class boundaries
- **Import resolution**: Includes relevant import statements

### `backend/modules/file_watcher.py`
- **File system monitoring**: Watches for file changes
- **Event handling**: Processes create, modify, delete events
- **Debouncing**: Prevents excessive processing
- **Pattern matching**: Ignores files based on patterns

### `backend/modules/index_sync.py`
- **Watcher management**: Manages multiple repository watchers
- **Index updates**: Handles incremental index updates
- **Thread safety**: Thread-safe singleton pattern
- **Error handling**: Graceful error recovery

---

## 📊 Project Status

### ✅ Completed Features (6/9 tasks)

1. **✅ Semantic Code Chunking** (Task 1)
   - Tree-sitter AST parsing
   - Regex fallback for unsupported languages
   - Function/class boundary detection

2. **✅ File Filtering & Ignore Patterns** (Task 3)
   - `.gitignore` support
   - Default ignore patterns
   - Configurable filtering

3. **✅ Enhanced Code Context** (Task 4)
   - Function boundary expansion
   - Import statement inclusion
   - Multi-language context retrieval

4. **✅ Code Refactoring Endpoint** (Task 5)
   - Dedicated `/refactor` endpoint
   - Before/after examples
   - Three input modes

5. **✅ Web UI/Frontend** (Task 6)
   - Modern chat interface
   - Streaming support
   - Analysis type selection

6. **✅ Automatic Code Change Tracking** (Task 8)
   - File system watching
   - Auto-sync on file changes
   - Incremental index updates

### ⏳ Pending Features (3/9 tasks)

1. **⏳ Agent System for Multi-step Reasoning** (Task 2)
   - Break down complex questions
   - Navigate codebase iteratively
   - Multi-step problem solving

2. **⏳ Multi-repo Support** (Task 7)
   - Index multiple repositories
   - Cross-repo queries
   - Unified search interface

3. **⏳ Large File Optimization** (Task 9)
   - Better handling of very large files
   - Streaming support for refactoring
   - Improved chunking strategy

---

## 🚀 Usage Examples

### Index a Repository
```powershell
$body = @{ repo_dir = "C:\Users\57811\my-portfolio" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/index_repo -Body $body -ContentType "application/json"
```

### Ask a Question
```powershell
$body = @{
    repo_dir = "C:\Users\57811\my-portfolio"
    question = "What is the main structure of this project?"
    analysis_type = "explain"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/chat -Body $body -ContentType "application/json"
```

### Get Refactoring Suggestions
```powershell
$body = @{
    repo_dir = "C:\Users\57811\my-portfolio"
    query = "function component"
    focus = "readability"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/refactor -Body $body -ContentType "application/json"
```

### Search Codebase
```powershell
$body = @{
    repo_dir = "C:\Users\57811\my-portfolio"
    query = "authentication"
    k = 5
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/search -Body $body -ContentType "application/json"
```

---

## 🔑 Key Technologies

- **Python 3.8+**: Backend language
- **Flask**: Web framework
- **FAISS**: Vector similarity search
- **Sentence Transformers**: Code embeddings
- **Tree-sitter**: AST parsing
- **Ripgrep**: Fast text search
- **Watchdog**: File system monitoring
- **OpenAI SDK**: LLM integration
- **TypeScript**: VS Code extension
- **HTML/CSS/JS**: Web UI

---

## 📁 Project Structure

```
smartcursor/
├── backend/
│   ├── modules/
│   │   ├── parser.py          # Code chunking & parsing
│   │   ├── vector_store.py    # FAISS index management
│   │   ├── search.py          # Hybrid search
│   │   ├── llm_api.py         # LLM integration
│   │   ├── context_retriever.py  # Context expansion
│   │   ├── file_watcher.py    # File monitoring
│   │   └── index_sync.py      # Auto-sync manager
│   ├── app.py                 # Flask API server
│   └── config.py              # Configuration
├── static/                    # Web UI
├── vscode-extension/          # VS Code extension
├── data/                      # Indexed data
├── test_*.py                  # Test scripts
└── requirements.txt           # Python dependencies
```

---

## 🎯 What Makes This Special?

1. **Semantic Understanding**: Uses AI to understand code meaning, not just text matching
2. **Automatic Sync**: Index stays up-to-date automatically when you edit files
3. **Multiple LLM Providers**: Supports DeepSeek, OpenAI, Anthropic, Qwen
4. **Comprehensive Search**: Combines vector and keyword search for best results
5. **Production Ready**: Error handling, logging, graceful degradation
6. **Extensible**: Easy to add new features and LLM providers

---

## 💡 Use Cases

- **Code Onboarding**: Understand large codebases quickly
- **Documentation**: Generate explanations and documentation
- **Code Review**: Get suggestions for improvements
- **Refactoring**: Automated refactoring suggestions
- **Debugging**: Find issues and understand code flow
- **Learning**: Learn from existing codebases

---

## 🔮 Future Enhancements (Pending Tasks)

1. **Multi-step Reasoning**: Break down complex questions into steps
2. **Multi-repo Support**: Query across multiple repositories
3. **Performance Optimization**: Better handling of large files
4. **Advanced Refactoring**: More sophisticated refactoring patterns
5. **Code Generation**: Generate new code based on examples
6. **Testing Suggestions**: Generate test cases for code

---

## 📝 Summary

This is a **production-ready, feature-rich code analysis system** that brings AI-powered code understanding to any codebase. It combines semantic search, natural language processing, and automatic synchronization to create a powerful development assistant.

**Progress: 6/9 core tasks completed (67%)** 🎉

The system is fully functional and can be used for real code analysis tasks. Remaining tasks add advanced features but the core functionality is solid and tested.

---

*Last Updated: November 2025*


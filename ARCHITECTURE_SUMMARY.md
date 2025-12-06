# Architecture & Directory Summary

## 🏗️ Simple Architecture Overview

This is a **Cursor-like AI code assistant** with two main parts:

1. **Backend (Python/Flask)** - The brain that processes code
2. **VS Code Extension (TypeScript)** - The interface you use in VS Code

```
User → VS Code Extension → Flask Backend → LLM API → Response
```

---

## 📁 Directory Structure (Simple)

```
smartcursor/
│
├── backend/                    # 🐍 Python Backend (The Brain)
│   ├── app.py                  # Main Flask server (all API endpoints)
│   ├── config.py               # Configuration (API keys, settings)
│   │
│   └── modules/                # Feature modules (organized by function)
│       ├── parser.py           # Parse code into chunks
│       ├── vector_store.py     # FAISS vector database
│       ├── search.py           # Hybrid search (keyword + semantic)
│       ├── llm_api.py          # Talk to AI (DeepSeek/OpenAI/etc)
│       ├── cache.py            # Caching system
│       ├── error_handler.py    # Error handling & retry logic
│       ├── privacy.py          # Privacy mode
│       ├── code_completion.py  # Inline code suggestions
│       ├── code_generation.py  # Generate new code
│       ├── test_generation.py  # Generate tests
│       ├── documentation_generation.py  # Generate docs
│       └── ... (25 modules total)
│
├── vscode-extension/           # 🔌 VS Code Extension (The Interface)
│   ├── src/
│   │   └── extension.ts        # Main extension code
│   ├── package.json            # Extension manifest
│   └── out/                    # Compiled JavaScript
│
├── data/                       # 💾 Stored Data
│   ├── index/                  # FAISS indexes (one per repo)
│   ├── cache/                  # Cache files (LLM, search, embeddings)
│   └── repos/                  # Repository metadata
│
├── static/                     # 🌐 Web UI (optional)
│   ├── index.html              # Web interface
│   └── js/app.js               # Frontend JavaScript
│
└── test_*.py                   # 🧪 Test files
```

---

## 🧩 How It Works (Simple Flow)

### 1. **Indexing** (One-time setup)
```
Code Repository
    ↓
parser.py (chunks code)
    ↓
vector_store.py (creates embeddings)
    ↓
FAISS Index (stored in data/index/)
```

### 2. **Searching** (When you ask questions)
```
User Question
    ↓
search.py (finds relevant code)
    ├── ripgrep (keyword search)
    └── FAISS (semantic search)
    ↓
Fused Results
```

### 3. **Answering** (AI generates response)
```
Search Results + User Question
    ↓
llm_api.py (sends to AI)
    ↓
AI Response (with code citations)
```

### 4. **Caching** (Speed optimization)
```
LLM Response → cache.py → data/cache/
Next time: Check cache first (50-80% faster!)
```

---

## 🔑 Key Components

### Backend Modules (What Each Does)

| Module | Purpose |
|--------|---------|
| `parser.py` | Splits code into chunks (functions, classes) |
| `vector_store.py` | Stores code as searchable vectors (FAISS) |
| `search.py` | Finds code (keyword + semantic search) |
| `llm_api.py` | Talks to AI (DeepSeek/OpenAI/etc) |
| `cache.py` | Caches responses (faster, cheaper) |
| `error_handler.py` | Handles errors, retries, rate limiting |
| `privacy.py` | Privacy mode (no code storage) |
| `code_completion.py` | Inline code suggestions (Tab autocomplete) |
| `code_generation.py` | Generates new code |
| `test_generation.py` | Generates tests |
| `documentation_generation.py` | Generates docs |
| `code_review.py` | Reviews code for bugs/issues |
| `smart_context.py` | Smart context management |
| `file_watcher.py` | Watches files for changes |
| `index_sync.py` | Auto-updates index when files change |

### VS Code Extension

| File | Purpose |
|------|---------|
| `extension.ts` | Main extension code (commands, UI) |
| `package.json` | Extension configuration |

---

## 🔄 Data Flow

```
1. User types in VS Code
   ↓
2. Extension sends request to Flask backend
   ↓
3. Backend searches codebase (vector + keyword)
   ↓
4. Backend sends code + question to AI
   ↓
5. AI generates answer
   ↓
6. Backend caches response (optional)
   ↓
7. Extension displays answer to user
```

---

## 📊 Architecture Layers

```
┌─────────────────────────────────────┐
│   VS Code Extension (Frontend)     │
│   - Commands, UI, User Interaction  │
└──────────────┬──────────────────────┘
               │ HTTP API
┌──────────────▼──────────────────────┐
│   Flask Backend (app.py)            │
│   - API Endpoints                    │
│   - Request Handling                │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────┐         ┌──────▼─────┐
│ Modules│         │   Data     │
│ (Logic)│         │  Storage   │
└───┬────┘         └────────────┘
    │
┌───▼──────────────┐
│  External APIs  │
│  (LLM Services) │
└─────────────────┘
```

---

## 🗂️ Important Directories

### `backend/modules/` - Feature Modules
- Each file = one feature/functionality
- Organized by purpose (search, LLM, caching, etc.)
- Reusable across endpoints

### `data/` - Persistent Storage
- `data/index/` - FAISS indexes (one folder per repo)
- `data/cache/` - Cache files (LLM, search, embeddings)
- `data/repos/` - Repository metadata

### `vscode-extension/` - VS Code Integration
- TypeScript extension code
- Commands, UI, integration with VS Code API

### `static/` - Web UI (Optional)
- HTML/CSS/JS for web interface
- Alternative to VS Code extension

---

## 🔌 API Endpoints (Main Ones)

| Endpoint | Purpose |
|----------|---------|
| `POST /index_repo` | Index a repository |
| `POST /search` | Search codebase |
| `POST /chat` | Ask questions (main feature) |
| `POST /refactor` | Get refactoring suggestions |
| `POST /generate` | Generate new code |
| `POST /completion` | Inline code completion |
| `POST /generate_tests` | Generate tests |
| `POST /generate_docs` | Generate documentation |
| `POST /edit` | Edit code directly |
| `POST /review` | Code review |
| `GET /privacy/status` | Privacy mode status |
| `GET /cache/stats` | Cache statistics |

---

## 🎯 Key Concepts

### 1. **Semantic Search**
- Code → Vectors → FAISS Index
- Find code by meaning, not just keywords

### 2. **Hybrid Search**
- Keyword search (ripgrep) + Semantic search (FAISS)
- Best of both worlds

### 3. **Caching**
- Store LLM responses
- 50-80% cost reduction
- Much faster responses

### 4. **Privacy Mode**
- No code storage when enabled
- GDPR compliance
- Enterprise-ready

### 5. **Auto-Sync**
- Watches files for changes
- Auto-updates index
- No manual re-indexing needed

---

## 📝 Configuration Files

| File | Purpose |
|------|---------|
| `.env` | API keys, settings (not in git) |
| `requirements.txt` | Python dependencies |
| `package.json` | VS Code extension config |
| `config.py` | Backend configuration |

---

## 🚀 How to Run

1. **Backend**: `python -m backend.app` (starts Flask server)
2. **Extension**: Load `vscode-extension/` in VS Code
3. **Web UI**: Open `http://127.0.0.1:5050` in browser

---

## 💡 Simple Mental Model

Think of it like a **smart code search engine**:

1. **Index** = Like Google indexing websites
2. **Search** = Like Google search (but for code)
3. **AI** = Like ChatGPT (but understands your code)
4. **Cache** = Like browser cache (faster next time)

---

*This is a simplified overview. See individual module files for details.*


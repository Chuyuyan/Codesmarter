# Code Analysis System - Usage Guide

A Cursor-like code analysis system that uses AI to understand and analyze your codebase.

## Setup

1. **Copy `.env.example` to `.env`**:
   ```bash
   cp .env.example .env
   ```

2. **Configure your API keys in `.env`**:
   - For DeepSeek (recommended): Set `LLM_PROVIDER=deepseek` and add your `DEEPSEEK_API_KEY`
   - For OpenAI: Set `LLM_PROVIDER=openai` and add your `OPENAI_API_KEY`
   - For Anthropic: Set `LLM_PROVIDER=anthropic` and add your `ANTHROPIC_API_KEY`

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the server**:
   ```bash
   python backend/app.py
   ```

## API Endpoints

### 1. Index Repository (`POST /index_repo`)

Index your codebase for analysis. This must be done first.

**Request:**
```json
{
  "repo_dir": "C:\\Users\\57811\\my-portfolio"
}
```

**Response:**
```json
{
  "ok": true,
  "repo_id": "my-portfolio",
  "chunks": 1234
}
```

**PowerShell Example:**
```powershell
$body = @{ repo_dir = "C:\Users\57811\my-portfolio" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/index_repo -Body $body -ContentType "application/json"
```

### 2. Chat / Query (`POST /chat`) ⭐ Main Endpoint

Ask questions about your code. This combines search + LLM in one call (like Cursor).

**Request:**
```json
{
  "repo_dir": "C:\\Users\\57811\\my-portfolio",
  "question": "How does user authentication work?",
  "analysis_type": "explain",  // Options: "explain", "refactor", "debug", "optimize"
  "stream": false,  // Set to true for streaming responses
  "top_k": 6
}
```

**Response:**
```json
{
  "ok": true,
  "answer": "The authentication system uses JWT tokens...",
  "evidences": [...],
  "citations": [
    {"file": "auth.py", "start": 10, "end": 25}
  ],
  "repo_id": "my-portfolio"
}
```

**PowerShell Example:**
```powershell
$body = @{
  repo_dir = "C:\Users\57811\my-portfolio"
  question = "How does authentication work?"
  analysis_type = "explain"
} | ConvertTo-Json

$result = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/chat -Body $body -ContentType "application/json"
$result.answer
```

### 3. Search Code (`POST /search`)

Search for code snippets without LLM analysis.

**Request:**
```json
{
  "repo_dir": "C:\\Users\\57811\\my-portfolio",
  "query": "authentication",
  "k": 6
}
```

### 4. Legacy Answer (`POST /answer`)

Legacy endpoint - use `/chat` instead.

## Analysis Types

The `/chat` endpoint supports different analysis types:

- **`explain`** (default): Explain what the code does
- **`refactor`**: Suggest refactoring improvements
- **`debug`**: Help identify bugs and issues
- **`optimize`**: Suggest performance optimizations

## Workflow (Like Cursor)

1. **Index your repository** once:
   ```bash
   POST /index_repo
   ```

2. **Ask questions** about your code:
   ```bash
   POST /chat
   {
     "repo_dir": "...",
     "question": "How does X work?",
     "analysis_type": "explain"
   }
   ```

3. **Get intelligent answers** with code citations and references.

## Streaming Responses

Set `"stream": true` in the `/chat` request to get real-time streaming responses (like Cursor):

```powershell
$body = @{
  repo_dir = "C:\Users\57811\my-portfolio"
  question = "Explain the main architecture"
  stream = $true
} | ConvertTo-Json

# Streaming response (Server-Sent Events)
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/chat -Body $body -ContentType "application/json" -Headers @{"Accept"="text/event-stream"}
```

## Examples

### Explain Code
```json
{
  "repo_dir": "C:\\Users\\57811\\my-portfolio",
  "question": "How does the user login function work?",
  "analysis_type": "explain"
}
```

### Refactor Code
```json
{
  "repo_dir": "C:\\Users\\57811\\my-portfolio",
  "question": "How can I improve this code?",
  "analysis_type": "refactor"
}
```

### Debug Code
```json
{
  "repo_dir": "C:\\Users\\57811\\my-portfolio",
  "question": "Are there any potential bugs in this code?",
  "analysis_type": "debug"
}
```

## Architecture

- **Vector Store**: FAISS for semantic code search
- **Keyword Search**: Ripgrep for fast text search
- **Hybrid Search**: Combines both for best results
- **LLM Integration**: Supports DeepSeek, OpenAI, Anthropic, Qwen
- **Code Analysis**: Multiple analysis types (explain, refactor, debug, optimize)

## Tips

- Index large repositories can take 1-5 minutes
- Use `stream: true` for better UX on long responses
- The system automatically combines vector search + keyword search for better results
- All responses include code citations for transparency


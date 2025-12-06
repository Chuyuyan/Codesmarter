# Quick Start Guide - Cursor-like Code Analysis System

## Step-by-Step Setup

### Step 1: Configure API Keys

Create a `.env` file in the project root:

```env
# Use DeepSeek (recommended)
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key_here

# Or use OpenAI
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your_api_key_here
```

### Step 2: Start the Server

```bash
python backend/app.py
```

Server will start on `http://127.0.0.1:5050`

### Step 3: Index Your Repository

```powershell
$body = @{ repo_dir = "C:\Users\57811\my-portfolio" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/index_repo -Body $body -ContentType "application/json"
```

Wait for indexing to complete (may take 1-5 minutes for large repos).

### Step 4: Ask Questions About Your Code

```powershell
$body = @{
  repo_dir = "C:\Users\57811\my-portfolio"
  question = "How does authentication work in this codebase?"
  analysis_type = "explain"
} | ConvertTo-Json

$result = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/chat -Body $body -ContentType "application/json"
Write-Host $result.answer
```

## Main Endpoints

### `/chat` - Main Endpoint (Like Cursor)
- Combines code search + AI analysis in one call
- Supports: explain, refactor, debug, optimize
- Optional streaming responses

### `/index_repo` - Index Repository
- Must be called first to analyze a repository
- Creates vector embeddings for semantic search

### `/search` - Search Code Only
- Just searches code without AI analysis

## Analysis Types

- **`explain`** (default): Explain what the code does
- **`refactor`**: Suggest refactoring improvements  
- **`debug`**: Help identify bugs and issues
- **`optimize`**: Suggest performance optimizations

## Example Questions

```powershell
# Explain code
$body = @{
  repo_dir = "C:\Users\57811\my-portfolio"
  question = "How does the user login function work?"
  analysis_type = "explain"
} | ConvertTo-Json

# Refactor code
$body = @{
  repo_dir = "C:\Users\57811\my-portfolio"
  question = "How can I improve this authentication code?"
  analysis_type = "refactor"
} | ConvertTo-Json

# Debug code
$body = @{
  repo_dir = "C:\Users\57811\my-portfolio"
  question = "Are there any potential bugs in the auth module?"
  analysis_type = "debug"
} | ConvertTo-Json
```

## How It Works

1. **Indexing**: Your code is split into chunks and embedded as vectors
2. **Hybrid Search**: Combines vector search (semantic) + ripgrep (keyword)
3. **AI Analysis**: Relevant code is sent to LLM (DeepSeek/OpenAI/etc.) for analysis
4. **Response**: Returns answer with code citations

This is similar to how Cursor analyzes your codebase!


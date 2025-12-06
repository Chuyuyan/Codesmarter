# Code Analysis Assistant - Cursor-like System

A powerful code analysis system that uses AI to understand and analyze your codebase, similar to Cursor.

## 🚀 Quick Start

### 1. Setup (First Time Only)

```powershell
# Create virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_deepseek_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
```

### 3. Start the Server

**Option A: Using PowerShell Script**
```powershell
.\.venv\Scripts\Activate.ps1
python backend/app.py
```

**Option B: Using Batch File**
```cmd
start_server.bat
```

**Option C: Using PowerShell Script**
```powershell
.\start_server.ps1
```

### 4. Use the Web Interface

Open your browser and go to:
```
http://127.0.0.1:5050
```

## 📋 Features

- **Index Repositories**: Index your codebase for analysis
- **Chat Interface**: Ask questions about your code
- **Semantic Chunking**: Intelligent code understanding
- **File Filtering**: Excludes node_modules, .git, build artifacts
- **Multiple Analysis Types**: explain, refactor, debug, optimize
- **Code Citations**: See exactly where answers come from

## 🔧 API Endpoints

- `GET /` - Web UI
- `POST /index_repo` - Index a repository
- `POST /chat` - Ask questions about code
- `POST /search` - Search codebase
- `GET /health` - Health check

## 📚 Documentation

See `USAGE.md` for detailed API documentation.

See `QUICKSTART.md` for quick start guide.

## 🛠️ Troubleshooting

**ModuleNotFoundError: No module named 'flask'**
- Make sure you've activated the virtual environment: `.\.venv\Scripts\Activate.ps1`
- Install dependencies: `pip install -r requirements.txt`

**Authentication Error**
- Check your `.env` file has valid API keys
- Verify DeepSeek API key is correct
- Restart the server after changing `.env`

**Port Already in Use**
- Change the port in `backend/app.py` or use a different port
- Or stop the existing server on port 5050


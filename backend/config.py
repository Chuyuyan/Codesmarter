# import os
# from dotenv import load_dotenv
# load_dotenv()

# OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
# OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
# OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "qwen2.5-coder-7b-instruct")

# CHUNK_LINES = 120          # fallback 切片行数
# TOP_K_RG    = 20           # ripgrep 初筛
# TOP_K_EMB   = 40           # 向量召回
# TOP_K_FINAL = 6            # 返回给前端的证据条数
# DATA_DIR    = "data"

import os
from dotenv import load_dotenv

# 加载 .env
load_dotenv()

# === 模型配置 ===
# Provider: "deepseek", "openai", "anthropic", "qwen", etc.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")

# DeepSeek Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# OpenAI Configuration
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4")

# Anthropic Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")

# Qwen Configuration
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen2.5-coder-7b-instruct")

# Default model for current provider
def get_default_model(provider):
    if provider == "deepseek":
        return DEEPSEEK_MODEL
    elif provider == "openai":
        return OPENAI_MODEL
    elif provider == "anthropic":
        return ANTHROPIC_MODEL
    elif provider == "qwen":
        return QWEN_MODEL
    return DEEPSEEK_MODEL

# Get default model based on provider, or use explicit LLM_MODEL env var
LLM_MODEL = os.getenv("LLM_MODEL") or get_default_model(LLM_PROVIDER)

# === 检索参数（默认值） ===
CHUNK_LINES = 120
TOP_K_RG    = 20
TOP_K_EMB   = 40
TOP_K_FINAL = 6

# === 数据路径 ===
DATA_DIR = os.getenv("DATA_DIR", "data")

# === Privacy Mode Configuration ===
# When enabled, no code will be stored in indexes or caches
# Set PRIVACY_MODE=true in .env to enable
PRIVACY_MODE = os.getenv("PRIVACY_MODE", "false").lower() in ("true", "1", "yes", "on")

# === 文件过滤配置 ===
# Default ignore patterns for indexing (similar to .gitignore)
DEFAULT_IGNORE_PATTERNS = [
    # Dependencies
    "node_modules/",
    "__pycache__/",
    ".venv/",
    "venv/",
    "env/",
    ".env",
    
    # Build artifacts
    ".next/",
    "dist/",
    "build/",
    "out/",
    ".nuxt/",
    ".output/",
    "target/",
    "bin/",
    "obj/",
    
    # Version control
    ".git/",
    ".svn/",
    ".hg/",
    
    # IDE/Editor
    ".vscode/",
    ".idea/",
    "*.swp",
    "*.swo",
    "*~",
    
    # OS files
    ".DS_Store",
    "Thumbs.db",
    
    # Logs and temp files
    "*.log",
    "*.tmp",
    ".cache/",
    "tmp/",
    "temp/",
    
    # Package manager
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
    
    # Coverage and test artifacts
    ".coverage",
    "coverage/",
    ".pytest_cache/",
    ".nyc_output/",
]

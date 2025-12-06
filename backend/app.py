from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
from pathlib import Path
import traceback
import json
import os
import sys

# Add project root to Python path so imports work when running from backend/
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.modules.parser import slice_repo
from backend.modules.vector_store import FaissStore
from backend.modules.search import ripgrep_candidates, fuse_results
from backend.modules.llm_api import answer_with_citations, analyze_code, stream_answer, suggest_refactoring
from backend.modules.context_retriever import expand_code_context, enrich_with_related_code
from backend.modules.index_sync import get_sync_manager
from backend.modules.multi_repo import (
    search_multiple_repos, index_multiple_repos, get_indexed_repos, repo_id_from_path
)
from backend.modules.question_decomposer import decompose_question, is_complex_question, analyze_decomposition
from backend.modules.iterative_agent import search_iterative_agent, IterativeSearchAgent
from backend.modules.large_file_handler import (
    chunk_large_file_semantically, get_file_size_category,
    extract_specific_sections, optimize_for_refactoring
)
from backend.modules.code_completion import generate_completion, generate_multiple_completions
from backend.modules.code_generation import generate_code
from backend.modules.composer import compose_multi_file_edit, apply_edits
from backend.modules.direct_edit import edit_code_directly, generate_diff_text
from backend.modules.test_generation import generate_tests
from backend.modules.documentation_generation import generate_documentation
from backend.modules.code_review import review_code, stream_review_code
from backend.modules.error_handler import (
    handle_errors, rate_limit, retry_with_backoff,
    validate_generated_code, RateLimitExceeded
)
from backend.modules.privacy import get_privacy_mode, is_privacy_mode_enabled
from backend.modules.repo_generator import generate_repository
from backend.config import DATA_DIR, TOP_K_EMB, TOP_K_FINAL
from backend.modules.database import init_database, db
from backend.modules.user_auth import UserAuth, require_auth
from flask import g
from flask_cors import CORS

# Get the project root directory (parent of backend)
BASE_DIR = project_root
STATIC_DIR = BASE_DIR / 'static'

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path='/static')

# Initialize CORS - allow all origins for development
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize database
init_database(app)

# Initialize user authentication
user_auth = UserAuth(db)

# Make user_auth available in request context
@app.before_request
def before_request():
    """Set up request context."""
    g.user_auth = user_auth

# Serve frontend
@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')

@app.route('/login')
def login_page():
    """Serve login page."""
    return send_from_directory(STATIC_DIR, 'login.html')

@app.route('/register')
def register_page():
    """Serve register page."""
    return send_from_directory(STATIC_DIR, 'register.html')

@app.route('/forgot-password')
def forgot_password_page():
    """Serve forgot password page."""
    return send_from_directory(STATIC_DIR, 'forgot-password.html')

@app.route('/reset-password')
def reset_password_page():
    """Serve reset password page."""
    return send_from_directory(STATIC_DIR, 'reset-password.html')

@app.route('/account')
def account_page():
    """Serve account page."""
    return send_from_directory(STATIC_DIR, 'account.html')

# repo_id_from_path is now imported from multi_repo module
# Keeping for backward compatibility if needed elsewhere
def repo_id_from_path_local(path: str) -> str:
    return Path(path).resolve().name  # 简单用目录名作 id

# 在 backend/app.py 顶部 app = Flask(__name__) 下面加
@app.get("/health")
def health():
    return jsonify(ok=True, port=5050)


@app.get("/repos")
@require_auth
def list_repos():
    """
    List all indexed repositories for the current user.
    Requires authentication.
    Returns information about all repositories that belong to the authenticated user.
    """
    try:
        user_id = request.current_user_id
        
        # Get user's repositories from database
        user_repos = user_auth.get_user_repositories(user_id)
        
        # Convert to list of dicts
        repos_list = [repo.to_dict() for repo in user_repos]
        
        return jsonify({
            "ok": True,
            "repos": repos_list,
            "count": len(repos_list)
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/decompose")
def decompose():
    """
    Decompose a complex question into smaller sub-questions.
    
    Accepts:
    - question: The complex question to decompose (required)
    - model: Optional model override
    - temperature: Optional temperature (default: 0.3)
    
    Returns:
    - List of sub-questions
    - Analysis of the decomposition
    """
    try:
        data = request.json or {}
        question = data.get("question")
        
        if not question:
            return jsonify({"ok": False, "error": "question is required"}), 400
        
        print(f"[decompose] Decomposing question: {question[:100]}...")
        
        # Check if question is complex
        is_complex = is_complex_question(question)
        
        # Decompose question
        sub_questions = decompose_question(
            question,
            model=data.get("model"),
            temperature=float(data.get("temperature", 0.3))
        )
        
        # Analyze decomposition
        analysis = analyze_decomposition(question, sub_questions)
        
        return jsonify({
            "ok": True,
            "original_question": question,
            "sub_questions": sub_questions,
            "is_complex": is_complex,
            "analysis": analysis
        })
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[decompose] Error: {error_msg}")
        print(f"[decompose] Traceback:\n{error_trace}")
        return jsonify({"ok": False, "error": error_msg, "traceback": error_trace}), 500


@app.post("/agent")
@require_auth
def agent():
    """
    Unified agent endpoint with multi-step reasoning.
    Combines all agent components: question decomposition, iterative search, 
    reasoning chain, and answer synthesis.
    
    Similar to /chat but with full agent capabilities:
    - Decomposes complex questions
    - Performs iterative codebase exploration
    - Tracks reasoning chain
    - Synthesizes comprehensive answers
    
    Supports both single-repo and multi-repo modes:
    - Single repo: repo_dir (string) - backward compatible
    - Multi-repo: repo_dirs (list) - searches across multiple repositories
    
    Accepts:
    - repo_dir: Single repository directory (optional if repo_dirs provided)
    - repo_dirs: List of repository directories (optional if repo_dir provided)
    - question: Complex question to answer (required)
    - decompose: Whether to decompose question (default: true)
    - sub_questions: Optional list of sub-questions (if decompose=false)
    - max_steps: Maximum number of search steps (default: 5)
    - results_per_step: Results per search step (default: 3)
    - stream: Whether to stream response (default: false)
    - analysis_type: Type of analysis (default: "explain")
    
    Returns:
    - synthesized_answer: Comprehensive answer from multi-step exploration
    - reasoning_chain: Complete reasoning chain data
    - reasoning_summary: Summary of exploration path
    - search_steps: Details of each search step
    - results: All code snippets found
    - citations: Code citations for the answer
    """
    try:
        data = request.json or {}
        repo_dir = data.get("repo_dir")
        repo_dirs = data.get("repo_dirs", [])
        question = data.get("question")
        decompose_flag = data.get("decompose", True)
        sub_questions = data.get("sub_questions", [])
        max_steps = data.get("max_steps", 5)
        results_per_step = int(data.get("results_per_step", 3))
        stream = data.get("stream", False)
        analysis_type = data.get("analysis_type")  # Optional - will auto-detect if not provided
        
        if not question and not sub_questions:
            return jsonify({"ok": False, "error": "question or sub_questions is required"}), 400
        
        # Auto-detect analysis type if not provided (use main question if available)
        if not analysis_type and question:
            from backend.modules.analysis_detector import detect_analysis_type
            analysis_type = detect_analysis_type(question, use_llm=False)
            print(f"[agent] Auto-detected analysis type: {analysis_type}")
        elif not analysis_type:
            analysis_type = "explain"  # Default for sub_questions only
            print(f"[agent] Using default analysis type: {analysis_type}")
        
        # Multi-repo mode
        if repo_dirs:
            if not isinstance(repo_dirs, list):
                return jsonify({"ok": False, "error": "repo_dirs must be a list"}), 400
            
            print(f"[agent] Multi-repo mode: {len(repo_dirs)} repositories")
            
            # For now, use first repo for iterative agent (can enhance later)
            # Or iterate through repos - for simplicity, use first repo
            primary_repo_dir = repo_dirs[0]
            repo_path = Path(primary_repo_dir)
            
            if not repo_path.exists():
                return jsonify({"ok": False, "error": f"repo_dir not found: {primary_repo_dir}"}), 400
            
            print(f"[agent] Using primary repo: {primary_repo_dir}")
            
            # Perform iterative search on primary repo
            result = search_iterative_agent(
                repo_dir=str(primary_repo_dir),
                question=question or "Search across codebase",
                decompose=decompose_flag and question is not None,
                max_steps=max_steps,
                results_per_step=results_per_step,
                base_dir=f"{DATA_DIR}/index"
            )
            
            # Note: For full multi-repo support, we'd need to enhance search_iterative_agent
            # For now, this provides agent capabilities on primary repo
            result["mode"] = "multi-repo"
            result["repo_dirs"] = repo_dirs
            result["primary_repo"] = primary_repo_dir
            
            # Override sub_questions if custom ones provided
            if sub_questions and not decompose_flag:
                result["sub_questions"] = sub_questions
            
            return jsonify(result)
        
        # Single repo mode
        if not repo_dir:
            return jsonify({"ok": False, "error": "repo_dir or repo_dirs must be provided"}), 400
        
        # Verify user owns the repo
        if not verify_user_owns_repo(user_auth, user_id, repo_dir):
            return jsonify({"ok": False, "error": "Repository not found or access denied"}), 403
        
        repo_path = Path(repo_dir)
        if not repo_path.exists():
            return jsonify({"ok": False, "error": f"repo_dir not found: {repo_dir}"}), 400
        
        print(f"[agent] Starting agent-based search for: {question[:100] if question else 'custom sub-questions'}...")
        
        # Perform iterative search with agent capabilities
        result = search_iterative_agent(
            repo_dir=str(repo_dir),
            question=question or "Search across codebase",
            decompose=decompose_flag and question is not None,
            max_steps=max_steps,
            results_per_step=results_per_step,
            base_dir=f"{DATA_DIR}/index"
        )
        
        # Override sub_questions if custom ones provided
        if sub_questions and not decompose_flag:
            result["sub_questions"] = sub_questions
        
        # Add mode indicator
        result["mode"] = "single-repo"
        
        # Format response similar to /chat for consistency
        synthesized_answer_data = result.get("synthesized_answer")
        
        if synthesized_answer_data and synthesized_answer_data.get("synthesized_answer"):
            result["answer"] = synthesized_answer_data["synthesized_answer"]
            result["citations"] = [
                {"file": r.get("file"), "start": r.get("start"), "end": r.get("end"), "repo_id": r.get("repo_id")}
                for r in result.get("results", [])[:10]
            ]
        
        return jsonify(result)
        
    except ValueError as e:
        # Repository not indexed
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[agent] Error: {error_msg}")
        print(f"[agent] Traceback:\n{error_trace}")
        return jsonify({"ok": False, "error": error_msg, "traceback": error_trace}), 500


@app.post("/search_iterative")
def search_iterative():
    """
    Perform iterative search across a codebase using decomposed sub-questions.
    
    Accepts:
    - repo_dir: Repository directory (required)
    - question: Complex question to decompose and search (required)
    - decompose: Whether to decompose question (default: true)
    - sub_questions: Optional list of sub-questions (if decompose=false)
    - max_steps: Maximum number of search steps (default: all sub-questions)
    - results_per_step: Results per step (default: 6)
    
    Returns:
    - All results from iterative searches
    - Search steps information
    - Summary of the iterative process
    """
    try:
        data = request.json or {}
        repo_dir = data.get("repo_dir")
        question = data.get("question")
        decompose_flag = data.get("decompose", True)
        sub_questions = data.get("sub_questions", [])
        max_steps = data.get("max_steps")
        results_per_step = int(data.get("results_per_step", TOP_K_FINAL))
        
        if not repo_dir:
            return jsonify({"ok": False, "error": "repo_dir is required"}), 400
        
        if not question and not sub_questions:
            return jsonify({"ok": False, "error": "question or sub_questions is required"}), 400
        
        repo_path = Path(repo_dir)
        if not repo_path.exists():
            return jsonify({"ok": False, "error": f"repo_dir not found: {repo_dir}"}), 400
        
        print(f"[search_iterative] Starting iterative search for: {question[:100] if question else 'custom sub-questions'}...")
        
        # Use provided sub-questions or decompose
        if sub_questions and not decompose_flag:
            final_sub_questions = sub_questions
        elif question:
            final_sub_questions = None  # Will be decomposed in search_iterative_agent
        else:
            return jsonify({"ok": False, "error": "Must provide question or sub_questions"}), 400
        
        # Perform iterative search
        result = search_iterative_agent(
            repo_dir=str(repo_dir),
            question=question or "Search across codebase",
            decompose=decompose_flag and question is not None,
            max_steps=max_steps,
            results_per_step=results_per_step,
            base_dir=f"{DATA_DIR}/index"
        )
        
        # Override sub_questions if custom ones were provided
        if sub_questions and not decompose_flag:
            result["sub_questions"] = sub_questions
        
        return jsonify(result)
        
    except ValueError as e:
        # Repository not indexed
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[search_iterative] Error: {error_msg}")
        print(f"[search_iterative] Traceback:\n{error_trace}")
        return jsonify({"ok": False, "error": error_msg, "traceback": error_trace}), 500


@app.post("/index_repo")
@require_auth
def index_repo():
    """
    Index one or more repositories.
    
    Accepts:
    - repo_dir: Single repository directory (backward compatible)
    - repo_dirs: List of repository directories (multi-repo mode)
    
    Returns:
    - Single repo mode: {ok, repo_id, chunks}
    - Multi-repo mode: {ok, repos: [{repo_id, repo_dir, ok, chunks/error}]}
    """
    try:
        if not request.json:
            return jsonify({"ok": False, "error": "No JSON body provided"}), 400
        
        # Support both single repo and multi-repo
        repo_dir = request.json.get("repo_dir")
        repo_dirs = request.json.get("repo_dirs", [])
        
        # Multi-repo mode
        if repo_dirs:
            if not isinstance(repo_dirs, list):
                return jsonify({"ok": False, "error": "repo_dirs must be a list"}), 400
            
            print(f"[index_repo] Indexing {len(repo_dirs)} repositories...")
            result = index_multiple_repos(repo_dirs, base_dir=f"{DATA_DIR}/index")
            
            # Associate repos with user and start watching
            user_id = request.current_user_id
            try:
                sync_manager = get_sync_manager()
                for repo_info in result["repos"]:
                    if repo_info.get("ok"):
                        repo_id = repo_info.get("repo_id")
                        repo_dir = repo_info.get("repo_dir", "")
                        chunks = repo_info.get("chunks", 0)
                        
                        # Associate with user
                        user_auth.add_user_repository(
                            user_id=user_id,
                            repo_id=repo_id,
                            repo_path=repo_dir,
                            repo_name=repo_id
                        )
                        
                        # Update index status
                        user_auth.update_repository_index_status(
                            user_id=user_id,
                            repo_id=repo_id,
                            is_indexed=True,
                            chunks_count=chunks
                        )
                        
                        # Start watching
                        sync_manager.watch_repo(
                            repo_dir,
                            repo_id,
                            base_dir=f"{DATA_DIR}/index"
                        )
                print(f"[index_repo] Started auto-sync for indexed repositories (user: {user_id})")
            except Exception as e:
                print(f"[index_repo] Warning: Could not start auto-sync: {e}")
            
            return jsonify(result)
        
        # Single repo mode (backward compatible)
        if not repo_dir:
            return jsonify({"ok": False, "error": "repo_dir or repo_dirs must be provided"}), 400
        
        # Verify user owns the repo
        if not verify_user_owns_repo(user_auth, user_id, repo_dir):
            return jsonify({"ok": False, "error": "Repository not found or access denied"}), 403
        
        repo_path = Path(repo_dir)
        if not repo_path.exists():
            return jsonify({"ok": False, "error": f"repo_dir not found: {repo_dir}"}), 400
        
        # Check privacy mode for storage type
        privacy_mode = get_privacy_mode()
        use_in_memory = privacy_mode.use_in_memory_storage()
        
        if use_in_memory:
            print(f"[index_repo] Privacy mode enabled - Using in-memory storage (RAM only)")
        else:
            print(f"[index_repo] Using disk storage")
        
        print(f"[index_repo] Starting indexing for: {repo_dir}")
        rid = repo_id_from_path(repo_dir)
        print(f"[index_repo] Repo ID: {rid}")
        
        print(f"[index_repo] Slicing repository...")
        chunks = slice_repo(repo_dir)
        print(f"[index_repo] Found {len(chunks)} chunks")
        
        print(f"[index_repo] Creating vector store...")
        store = FaissStore(rid, base_dir=f"{DATA_DIR}/index", in_memory=use_in_memory)
        print(f"[index_repo] Building index...")
        store.build(chunks)
        print(f"[index_repo] Index built successfully")
        
        # 缓存切片（可选）
        Path(f"{DATA_DIR}/repos/{rid}").mkdir(parents=True, exist_ok=True)
        
        # Start watching repository for changes (auto-sync)
        try:
            sync_manager = get_sync_manager()
            sync_manager.watch_repo(repo_dir, rid, base_dir=f"{DATA_DIR}/index")
            print(f"[index_repo] Started auto-sync for repository")
        except Exception as e:
            print(f"[index_repo] Warning: Could not start auto-sync: {e}")
        
        result = {"ok": True, "repo_id": rid, "chunks": len(chunks)}
        print(f"[index_repo] Success: {result}")
        return jsonify(result)
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[index_repo] Error: {error_msg}")
        print(f"[index_repo] Traceback:\n{error_trace}")
        return jsonify({"ok": False, "error": error_msg, "traceback": error_trace}), 500

@app.post("/search")
@require_auth
@rate_limit("search", max_requests=200, time_window=60)
@handle_errors()
def search():
    """
    Search codebase for relevant code snippets (hybrid: ripgrep + vector search).
    
    Supports both single-repo and multi-repo modes:
    - Single repo: repo_dir (string) - backward compatible
    - Multi-repo: repo_dirs (list) - searches across multiple repositories
    
    Parameters:
    - repo_dir: Single repository directory (optional if repo_dirs provided)
    - repo_dirs: List of repository directories (optional if repo_dir provided)
    - query: Search query (required)
    - k: Maximum number of results (optional, default: 6)
    """
    try:
        data = request.json or {}
        repo_dir = data.get("repo_dir")
        repo_dirs = data.get("repo_dirs", [])
        query = data.get("query")
        k = int(data.get("k", TOP_K_FINAL))
        
        if not query:
            return jsonify({"ok": False, "error": "query is required"}), 400
        
        # Multi-repo mode
        if repo_dirs:
            if not isinstance(repo_dirs, list):
                return jsonify({"ok": False, "error": "repo_dirs must be a list"}), 400
            
            print(f"[search] Searching across {len(repo_dirs)} repositories...")
            results = search_multiple_repos(repo_dirs, query, top_k=k, base_dir=f"{DATA_DIR}/index")
            
            return jsonify({
                "ok": True,
                "results": results,
                "count": len(results),
                "mode": "multi-repo",
                "repos_searched": len(repo_dirs)
            })
        
        # Single repo mode (backward compatible)
        if not repo_dir:
            return jsonify({"ok": False, "error": "repo_dir or repo_dirs must be provided"}), 400
        
        rid = repo_id_from_path(repo_dir)
        store = FaissStore(rid, base_dir=f"{DATA_DIR}/index")
        
        if not store.index_path.exists():
            return jsonify({
                "ok": False,
                "error": f"Repository not indexed. Please index it first using /index_repo",
                "repo_id": rid
            }), 400
        
        # Check privacy mode - skip caching if privacy mode enabled
        privacy_mode = get_privacy_mode()
        use_search_cache = privacy_mode.should_cache()
        
        # Check search result cache
        cached_results = None
        if use_search_cache:
            try:
                from backend.modules.cache import get_search_cache
                search_cache = get_search_cache(cache_dir=f"{DATA_DIR}/cache/search")
                cached_results = search_cache.get(query, repo_dir, search_type="hybrid")
                if cached_results:
                    print(f"[search] Cache HIT for query: {query[:50]}...")
                    # Add repo_id for consistency
                    for result in cached_results:
                        result["repo_id"] = rid
                        result["repo_dir"] = repo_dir
                    
                    return jsonify({
                        "ok": True,
                        "results": cached_results[:k],  # Apply k limit
                        "count": len(cached_results[:k]),
                        "mode": "single-repo",
                        "repo_id": rid,
                        "cached": True
                    })
                print(f"[search] Cache MISS for query: {query[:50]}...")
            except Exception as e:
                print(f"[search] Cache error (continuing without cache): {e}")
        else:
            print(f"[search] Privacy mode enabled - skipping cache")
        
        store.load()
        rg = ripgrep_candidates(query, repo_dir)
        vec = store.query(query, k=TOP_K_EMB)
        fused = fuse_results(rg, vec, top_k=k)
        
        # Cache the results (only if privacy mode allows)
        if use_search_cache:
            try:
                from backend.modules.cache import get_search_cache
                search_cache = get_search_cache(cache_dir=f"{DATA_DIR}/cache/search")
                search_cache.set(query, repo_dir, fused, search_type="hybrid")
                print(f"[search] Cached results for query: {query[:50]}...")
            except Exception as e:
                print(f"[search] Error caching results: {e}")
        else:
            print(f"[search] Privacy mode enabled - not caching results")
        
        # Add repo_id for consistency
        for result in fused:
            result["repo_id"] = rid
            result["repo_dir"] = repo_dir
        
        return jsonify({
            "ok": True,
            "results": fused,
            "count": len(fused),
            "mode": "single-repo",
            "repo_id": rid,
            "cached": False
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/chat")
@require_auth
@rate_limit("chat", max_requests=100, time_window=60)
@handle_errors()
def chat():
    """
    Unified chat endpoint (like Cursor) that combines search + LLM in one call.
    This is the main endpoint for code analysis and Q&A.
    
    Supports both single-repo and multi-repo modes:
    - Single repo: repo_dir (string) - backward compatible
    - Multi-repo: repo_dirs (list) - searches across multiple repositories
    """
    try:
        data = request.json or {}
        repo_dir = data.get("repo_dir")
        repo_dirs = data.get("repo_dirs", [])
        question = data.get("question") or data.get("query")
        analysis_type = data.get("analysis_type")  # Optional - will auto-detect if not provided
        stream = data.get("stream", False)
        top_k = int(data.get("top_k", TOP_K_FINAL))
        conversation_id = data.get("conversation_id")  # Optional - for conversation history
        clear_history = data.get("clear_history", False)  # Optional - clear conversation history
        
        if not question:
            return jsonify({"ok": False, "error": "question or query is required"}), 400
        
        # Handle conversation history
        conversation_history = None
        conversation = None
        if conversation_id:
            from backend.modules.conversation_history import get_conversation
            from backend.modules.privacy import get_privacy_mode
            
            privacy_mode = get_privacy_mode()
            use_in_memory = privacy_mode.use_in_memory_storage()
            
            conversation = get_conversation(conversation_id, in_memory=use_in_memory)
            
            if clear_history:
                conversation.clear()
                print(f"[chat] Cleared conversation history: {conversation_id}")
            else:
                # Get recent conversation history (within token limit)
                conversation_history = conversation.get_recent_messages(max_tokens=2000)
                print(f"[chat] Loaded {len(conversation_history)} previous messages from conversation: {conversation_id}")
        
        # Auto-detect analysis type if not provided
        if not analysis_type:
            from backend.modules.analysis_detector import detect_analysis_type
            analysis_type = detect_analysis_type(question, use_llm=False)
            print(f"[chat] Auto-detected analysis type: {analysis_type}")
        else:
            print(f"[chat] Using provided analysis type: {analysis_type}")
        
        print(f"[chat] Question: {question[:100]}...")
        print(f"[chat] Analysis type: {analysis_type}")
        
        # Handle "generate" analysis type - route to full-stack generator
        if analysis_type == "generate":
            # Check if this is a full-stack project request
            from backend.modules.full_stack_generator import detect_stack_from_description
            
            stack = detect_stack_from_description(question)
            is_full_stack = (
                "frontend" in question.lower() or 
                "backend" in question.lower() or 
                "full stack" in question.lower() or
                "fullstack" in question.lower() or
                any(kw in question.lower() for kw in ["react", "vue", "flask", "express", "database"])
            )
            
            if is_full_stack:
                # This is a full-stack project generation request
                # Return instructions to use /generate_project endpoint
                return jsonify({
                    "ok": True,
                    "answer": f"""I detected you want to generate a full-stack project!

Detected Stack:
- Frontend: {stack.get('frontend', 'react')}
- Backend: {stack.get('backend', 'flask')}
- Database: {stack.get('database', 'sqlite')}

To generate the complete project, please use the `/generate_project` endpoint with:
- description: Your project description
- repo_path: Where to create the project
- dry_run: true (to preview first)

Or continue this conversation and I'll help you build it step by step!""",
                    "analysis_type": "generate",
                    "detected_stack": stack,
                    "suggestion": "Use /generate_project endpoint for full project generation"
                })
        
        # Handle "generate" analysis type - project generation
        if analysis_type == "generate":
            return handle_project_generation_in_chat(question, repo_dir, conversation_history, stream)
        
        evidences = []
        repo_ids = []
        
        # Get user ID and verify ownership
        user_id = request.current_user_id
        from backend.modules.user_repo_helper import verify_user_owns_repo
        
        # Multi-repo mode
        if repo_dirs:
            if not isinstance(repo_dirs, list):
                return jsonify({"ok": False, "error": "repo_dirs must be a list"}), 400
            
            # Verify user owns all repos
            for repo_dir_path in repo_dirs:
                if not verify_user_owns_repo(user_auth, user_id, repo_dir_path):
                    return jsonify({"ok": False, "error": f"Repository not found or access denied: {repo_dir_path}"}), 403
            
            print(f"[chat] Searching across {len(repo_dirs)} repositories (user: {user_id})...")
            evidences = search_multiple_repos(repo_dirs, question, top_k=top_k, base_dir=f"{DATA_DIR}/index")
            repo_ids = list(set([e.get("repo_id") for e in evidences if e.get("repo_id")]))
            
            # Enhance evidences with better context (use first repo_dir for context expansion)
            if repo_dirs and evidences:
                first_repo_dir = repo_dirs[0]
                print(f"[chat] Enhancing code context with smart prioritization...")
                evidences = expand_code_context(
                    evidences,
                    first_repo_dir,
                    context_lines=15,
                    use_smart_context=True,
                    query=question,  # Use question for relevance scoring
                    max_tokens=8000
                )
        # Single repo mode (backward compatible)
        elif repo_dir:
            # Verify user owns the repo
            user_id = request.current_user_id
            from backend.modules.user_repo_helper import verify_user_owns_repo
            
            if not verify_user_owns_repo(user_auth, user_id, repo_dir):
                return jsonify({"ok": False, "error": "Repository not found or access denied"}), 403
            
            repo_path = Path(repo_dir)
            if not repo_path.exists():
                return jsonify({"ok": False, "error": f"repo_dir not found: {repo_dir}"}), 400
            
            # Get repo ID and load vector store
            rid = repo_id_from_path(repo_dir)
            store = FaissStore(rid, base_dir=f"{DATA_DIR}/index")
            
            if not store.index_path.exists():
                return jsonify({
                    "ok": False, 
                    "error": f"Repository not indexed. Please index it first using /index_repo",
                    "repo_id": rid
                }), 400
            
            store.load()
            
            # Search for relevant code (hybrid search: ripgrep + vector)
            print(f"[chat] Searching codebase...")
            rg_results = ripgrep_candidates(question, repo_dir)
            vec_results = store.query(question, k=TOP_K_EMB)
            evidences = fuse_results(rg_results, vec_results, top_k=top_k)
            
            # Add repo_id for consistency
            for evidence in evidences:
                evidence["repo_id"] = rid
                evidence["repo_dir"] = repo_dir
            
            # Enhance evidences with better context
            print(f"[chat] Enhancing code context with smart prioritization...")
            evidences = expand_code_context(
                evidences,
                repo_dir,
                context_lines=15,
                use_smart_context=True,
                query=question,  # Use question for relevance scoring
                max_tokens=8000
            )
            repo_ids = [rid]
        else:
            return jsonify({"ok": False, "error": "repo_dir or repo_dirs must be provided"}), 400
        
        print(f"[chat] Found {len(evidences)} relevant code snippets (with enhanced context)")
        
        if not evidences:
            return jsonify({
                "ok": True,
                "answer": "No relevant code found for your question. Try rephrasing or indexing the repository first.",
                "evidences": [],
                "citations": []
            })
        
        # Generate answer with LLM
        if stream:
            # Streaming response (like Cursor)
            def generate():
                try:
                    yield "data: " + json.dumps({"type": "start"}) + "\n\n"
                    answer_chunks = []
                    for chunk in stream_answer(question, evidences, conversation_history=conversation_history):
                        answer_chunks.append(chunk)
                        yield "data: " + json.dumps({"type": "chunk", "content": chunk}) + "\n\n"
                    
                    # Save conversation history
                    if conversation_id and conversation:
                        answer_text = "".join(answer_chunks)
                        conversation.add_message("user", question)
                        conversation.add_message("assistant", answer_text)
                    
                    yield "data: " + json.dumps({
                        "type": "done",
                        "citations": [{"file": e["file"], "start": e["start"], "end": e["end"], "repo_id": e.get("repo_id")} for e in evidences]
                    }) + "\n\n"
                except Exception as e:
                    yield "data: " + json.dumps({"type": "error", "error": str(e)}) + "\n\n"
            
            return Response(stream_with_context(generate()), mimetype='text/event-stream')
        else:
            # Non-streaming response
            print(f"[chat] Generating answer with LLM...")
            answer = analyze_code(question, evidences, analysis_type=analysis_type, conversation_history=conversation_history)
            
            # Save conversation history
            if conversation_id and conversation:
                conversation.add_message("user", question)
                conversation.add_message("assistant", answer)
            
            # Determine mode and repo info
            is_multi_repo = bool(repo_dirs)
            single_repo_id = None
            if not is_multi_repo and repo_dir:
                single_repo_id = repo_id_from_path(repo_dir)
            
            return jsonify({
                "ok": True,
                "answer": answer,
                "evidences": evidences,
                "citations": [{"file": e["file"], "start": e["start"], "end": e["end"], "repo_id": e.get("repo_id")} for e in evidences],
                "repo_ids": repo_ids,
                "repo_id": single_repo_id,
                "mode": "multi-repo" if is_multi_repo else "single-repo"
            })
    
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[chat] Error: {error_msg}")
        print(f"[chat] Traceback:\n{error_trace}")
        return jsonify({"ok": False, "error": error_msg, "traceback": error_trace}), 500


@app.post("/refactor")
def refactor():
    """
    Dedicated refactoring endpoint with before/after examples.
    
    Accepts:
    - repo_dir: Repository directory (required if using query/file_path)
    - query: Search query to find code to refactor (optional)
    - file_path: Specific file path to refactor (optional)
    - code_snippets: Direct code snippets to refactor (optional, list of dicts with 'file', 'start', 'end', 'snippet')
    - focus: Optional focus area (e.g., "performance", "readability", "design patterns", "maintainability")
    - top_k: Number of code snippets to analyze (default: 5)
    - stream: If true, stream the response (default: false)
    
    Returns:
    - If stream=false: Complete response with refactoring_suggestions, code_context, etc.
    - If stream=true: Server-Sent Events stream with chunks of refactoring suggestions
    """
    try:
        data = request.json or {}
        repo_dir = data.get("repo_dir")
        query = data.get("query")
        file_path = data.get("file_path")
        code_snippets = data.get("code_snippets")  # Direct snippets
        focus = data.get("focus", "")  # Optional focus area
        top_k = int(data.get("top_k", 5))
        
        # Validate input
        if code_snippets:
            # Use provided code snippets directly
            if not isinstance(code_snippets, list):
                return jsonify({"ok": False, "error": "code_snippets must be a list"}), 400
            evidences = code_snippets
        elif file_path:
            # Get specific file
            if not repo_dir:
                return jsonify({"ok": False, "error": "repo_dir is required when using file_path"}), 400
            
            repo_path = Path(repo_dir)
            if not repo_path.exists():
                return jsonify({"ok": False, "error": f"repo_dir not found: {repo_dir}"}), 400
            
            target_file = Path(file_path)
            if not target_file.is_absolute():
                target_file = repo_path / target_file
            
            if not target_file.exists():
                return jsonify({"ok": False, "error": f"file_path not found: {file_path}"}), 400
            
            # Load the file and handle based on size
            try:
                file_size_category = get_file_size_category(target_file)
                print(f"[refactor] File size category: {file_size_category}")
                
                # For large files, use semantic chunking
                if file_size_category in ["large", "very_large"]:
                    # Use semantic chunking to extract functions/classes
                    print(f"[refactor] Using semantic chunking for large file")
                    evidences = chunk_large_file_semantically(
                        target_file,
                        max_chunks=5,  # Get top 5 functions/classes
                        max_lines_per_chunk=200
                    )
                    
                    if not evidences:
                        # Fallback: use first portion of file
                        content = target_file.read_text(encoding="utf-8", errors="ignore")
                        lines = content.splitlines()
                        max_lines = 200
                        limited_content = "\n".join(lines[:max_lines])
                        evidences = [{
                            "file": str(target_file),
                            "start": 1,
                            "end": max_lines,
                            "snippet": limited_content + f"\n\n// ... (file truncated, showing first {max_lines} lines) ..."
                        }]
                else:
                    # Small/medium files: use full content
                    content = target_file.read_text(encoding="utf-8", errors="ignore")
                    lines = content.splitlines()
                    evidences = [{
                        "file": str(target_file),
                        "start": 1,
                        "end": len(lines),
                        "snippet": content
                    }]
            except Exception as e:
                return jsonify({"ok": False, "error": f"Error reading file: {str(e)}"}), 500
        elif query:
            # Search for code using query
            if not repo_dir:
                return jsonify({"ok": False, "error": "repo_dir is required when using query"}), 400
            
            repo_path = Path(repo_dir)
            if not repo_path.exists():
                return jsonify({"ok": False, "error": f"repo_dir not found: {repo_dir}"}), 400
            
            # Get repo ID and load vector store
            rid = repo_id_from_path(repo_dir)
            store = FaissStore(rid, base_dir=f"{DATA_DIR}/index")
            
            if not store.index_path.exists():
                return jsonify({
                    "ok": False,
                    "error": f"Repository not indexed. Please index it first using /index_repo",
                    "repo_id": rid
                }), 400
            
            store.load()
            
            # Search for relevant code
            print(f"[refactor] Searching for code to refactor: {query}")
            rg_results = ripgrep_candidates(query, repo_dir)
            vec_results = store.query(query, k=TOP_K_EMB)
            evidences = fuse_results(rg_results, vec_results, top_k=top_k)
            
            # Expand context for better refactoring suggestions (limit expansion for refactoring)
            # For refactoring, we want focused suggestions, so limit context expansion
            print(f"[refactor] Enhancing code context with smart prioritization...")
            evidences = expand_code_context(
                evidences,
                repo_dir,
                context_lines=10,
                use_smart_context=True,
                query=query if 'query' in locals() else None,  # Use query if available
                file_path=file_path if 'file_path' in locals() else None,  # Use file_path if available
                max_tokens=6000  # Lower for refactoring (more focused)
            )
        else:
            return jsonify({
                "ok": False,
                "error": "Must provide one of: code_snippets, file_path, or query"
            }), 400
        
        if not evidences:
            return jsonify({
                "ok": False,
                "error": "No code found to refactor. Try a different query or provide code_snippets."
            }), 404
        
        print(f"[refactor] Analyzing {len(evidences)} code snippet(s) for refactoring")
        if focus:
            print(f"[refactor] Focus area: {focus}")
        
        # Optimize evidences for refactoring (handles large files better)
        # Uses semantic chunking and token-aware optimization
        print(f"[refactor] Optimizing code snippets for refactoring...")
        evidences = optimize_for_refactoring(
            evidences,
            max_total_tokens=8000,  # Conservative token limit for refactoring
            prefer_semantic=True
        )
        print(f"[refactor] Optimized to {len(evidences)} snippet(s) for LLM processing")
        
        stream = data.get("stream", False)
        print(f"[refactor] Calling LLM for refactoring suggestions... (stream={stream})")
        
        if stream:
            # Streaming response
            from backend.modules.llm_api import stream_suggest_refactoring
            
            def generate():
                try:
                    yield "data: " + json.dumps({"type": "start"}) + "\n\n"
                    
                    # Collect all chunks for metadata
                    suggestion_chunks = []
                    for chunk in stream_suggest_refactoring(evidences, focus=focus, model=data.get("model"), temperature=float(data.get("temperature", 0.3))):
                        if chunk.startswith("Error:"):
                            yield "data: " + json.dumps({"type": "error", "error": chunk}) + "\n\n"
                            return
                        suggestion_chunks.append(chunk)
                        yield "data: " + json.dumps({"type": "chunk", "content": chunk}) + "\n\n"
                    
                    # Get metadata
                    refactoring_suggestions = "".join(suggestion_chunks)
                    
                    yield "data: " + json.dumps({
                        "type": "done",
                        "code_context": evidences,
                        "focus": focus,
                        "format": "markdown",
                        "count": len(evidences),
                        "suggestions_length": len(refactoring_suggestions)
                    }) + "\n\n"
                except Exception as e:
                    yield "data: " + json.dumps({"type": "error", "error": str(e)}) + "\n\n"
            
            return Response(stream_with_context(generate()), mimetype='text/event-stream')
        else:
            # Non-streaming response
            result = suggest_refactoring(evidences, focus=focus)
            print(f"[refactor] LLM response received")
            
            if not result.get("ok"):
                return jsonify(result), 500
            
            return jsonify({
                "ok": True,
                "refactoring_suggestions": result["refactoring_suggestions"],
                "code_context": evidences,
                "focus": focus,
                "format": "markdown",
                "count": len(evidences)
            })
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[refactor] Error: {error_msg}")
        print(f"[refactor] Traceback:\n{error_trace}")
        return jsonify({"ok": False, "error": error_msg, "traceback": error_trace}), 500


@app.post("/completion")
def completion():
    """
    Inline code completion endpoint (like Cursor's Tab feature).
    Generates code completions based on cursor position and context.
    
    Accepts:
    - file_path: Path to the file being edited (required)
    - file_content: Full content of the file (required)
    - cursor_line: Cursor line number (1-indexed) (required)
    - cursor_column: Cursor column number (1-indexed) (required)
    - repo_dir: Optional repository directory for codebase context
    - num_completions: Number of completion candidates (default: 1)
    - max_tokens: Maximum tokens for completion (default: 200)
    - model: Optional model override
    
    Returns:
    - completions: List of completion strings
    - primary_completion: Best completion (first one)
    """
    try:
        data = request.json or {}
        file_path = data.get("file_path")
        file_content = data.get("file_content", "")
        cursor_line = data.get("cursor_line")
        cursor_column = data.get("cursor_column")
        repo_dir = data.get("repo_dir")
        num_completions = int(data.get("num_completions", 1))
        max_tokens = int(data.get("max_tokens", 200))
        model = data.get("model")
        
        # Validate input
        if not file_path:
            return jsonify({"ok": False, "error": "file_path is required"}), 400
        
        if not file_content:
            return jsonify({"ok": False, "error": "file_content is required"}), 400
        
        if cursor_line is None or cursor_column is None:
            return jsonify({"ok": False, "error": "cursor_line and cursor_column are required"}), 400
        
        # Validate cursor position
        lines = file_content.splitlines()
        if cursor_line < 1 or cursor_line > len(lines) + 1:
            return jsonify({"ok": False, "error": f"cursor_line out of range (1-{len(lines)+1})"}), 400
        
        print(f"[completion] Generating completion for {Path(file_path).name}:{cursor_line}:{cursor_column}")
        
        # Generate completion(s)
        if num_completions > 1:
            completions = generate_multiple_completions(
                file_path,
                file_content,
                cursor_line,
                cursor_column,
                repo_dir=repo_dir,
                num_completions=num_completions,
                model=model
            )
        else:
            completion_text = generate_completion(
                file_path,
                file_content,
                cursor_line,
                cursor_column,
                repo_dir=repo_dir,
                model=model,
                max_tokens=max_tokens
            )
            completions = [completion_text] if completion_text else []
        
        if not completions:
            return jsonify({
                "ok": True,
                "completions": [],
                "primary_completion": "",
                "message": "No completion generated"
            })
        
        return jsonify({
            "ok": True,
            "completions": completions,
            "primary_completion": completions[0],
            "count": len(completions)
        })
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[completion] Error: {error_msg}")
        print(f"[completion] Traceback:\n{error_trace}")
        return jsonify({"ok": False, "error": error_msg, "traceback": error_trace}), 500


@app.post("/generate")
@handle_errors()
def generate():
    """
    Code generation endpoint - generates new code from natural language descriptions.
    Similar to Cursor's code generation feature.
    
    Accepts:
    - request: Natural language description of what to generate (required)
    - generation_type: Type of generation - "function", "class", "file", "test" (default: "function")
    - language: Target programming language (auto-detected from target_file if not provided)
    - target_file: Target file path (for context and language detection)
    - repo_dir: Repository directory (for codebase context)
    - code_to_test: Code to generate tests for (required if generation_type is "test")
    - model: Optional model override
    - max_tokens: Maximum tokens for generation (default: 2000)
    
    Returns:
    - generated_code: The generated code
    - language: Detected/generated language
    - generation_type: Type of generation
    - syntax_valid: Whether syntax is valid
    - syntax_error: Syntax error message if invalid
    """
    try:
        data = request.json or {}
        request_text = data.get("request")
        generation_type = data.get("generation_type", "function")
        language = data.get("language")
        target_file = data.get("target_file")
        repo_dir = data.get("repo_dir")
        code_to_test = data.get("code_to_test")
        model = data.get("model")
        max_tokens = int(data.get("max_tokens", 2000))
        
        # Validate input
        if not request_text:
            return jsonify({"ok": False, "error": "request is required"}), 400
        
        # Validate generation_type
        valid_types = ["function", "class", "file", "test"]
        if generation_type not in valid_types:
            return jsonify({
                "ok": False,
                "error": f"generation_type must be one of: {', '.join(valid_types)}"
            }), 400
        
        # Validate repo_dir if provided
        if repo_dir:
            repo_path = Path(repo_dir)
            if not repo_path.exists():
                return jsonify({"ok": False, "error": f"repo_dir not found: {repo_dir}"}), 400
        
        print(f"[generate] Generating {generation_type} for: {request_text[:80]}...")
        
        # Generate code
        result = generate_code(
            request=request_text,
            generation_type=generation_type,
            language=language,
            target_file=target_file,
            repo_dir=repo_dir,
            code_to_test=code_to_test,
            model=model,
            max_tokens=max_tokens
        )
        
        if not result.get("ok"):
            return jsonify(result), 500
        
        # Validate generated code syntax
        generated_code = result.get("generated_code", "")
        detected_language = result.get("language", language or "python")
        
        if generated_code and detected_language:
            is_valid, error_message = validate_generated_code(generated_code, detected_language)
            result["syntax_valid"] = is_valid
            if not is_valid:
                result["syntax_error"] = error_message
                # Don't fail, just warn - user can fix it
                print(f"[generate] Syntax validation warning: {error_message}")
            else:
                result["syntax_error"] = None
                print(f"[generate] Generated code syntax is valid")
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[generate] Error: {error_msg}")
        print(f"[generate] Traceback:\n{error_trace}")
        return jsonify({"ok": False, "error": error_msg, "traceback": error_trace}), 500


@app.post("/compose")
def compose():
    """
    Multi-file editing endpoint (Composer Mode).
    Similar to Cursor's Composer - edits multiple files simultaneously through natural language.
    
    Accepts:
    - request: Natural language description of changes (required)
    - repo_dir: Repository directory (required)
    - target_files: Optional list of specific files to edit (if None, AI determines)
    - dry_run: If true, return preview without applying changes (default: true)
    - apply: If true, apply changes to files (default: false, requires dry_run=false)
    - model: Optional model override
    - max_tokens: Maximum tokens for generation (default: 4000)
    
    Returns:
    - edits: List of file edits with diffs
    - summary: Summary of all changes
    - dependencies: Files that depend on each other
    - If dry_run=true: preview only (no changes applied)
    - If apply=true: results of applying changes
    """
    try:
        data = request.json or {}
        request_text = data.get("request")
        repo_dir = data.get("repo_dir")
        target_files = data.get("target_files")  # Optional list
        dry_run = data.get("dry_run", True)  # Default to preview only
        apply_changes = data.get("apply", False)  # Default to false
        model = data.get("model")
        max_tokens = int(data.get("max_tokens", 4000))
        
        # Validate input
        if not request_text:
            return jsonify({"ok": False, "error": "request is required"}), 400
        
        if not repo_dir:
            return jsonify({"ok": False, "error": "repo_dir is required"}), 400
        
        repo_path = Path(repo_dir)
        if not repo_path.exists():
            return jsonify({"ok": False, "error": f"repo_dir not found: {repo_dir}"}), 400
        
        print(f"[compose] Composing multi-file edit for: {request_text[:80]}...")
        print(f"[compose] Target files: {target_files or 'AI will determine'}")
        print(f"[compose] Dry run: {dry_run}, Apply: {apply_changes}")
        
        # Compose edits
        result = compose_multi_file_edit(
            request=request_text,
            repo_dir=repo_dir,
            target_files=target_files,
            model=model,
            max_tokens=max_tokens
        )
        
        if not result.get("ok"):
            return jsonify(result), 500
        
        # If apply_changes is true and dry_run is false, apply the edits
        if apply_changes and not dry_run:
            print(f"[compose] Applying edits to {len(result['edits'])} files...")
            apply_result = apply_edits(result["edits"], repo_dir, dry_run=False)
            result["apply_result"] = apply_result
            result["changes_applied"] = apply_result.get("files_changed", 0)
            result["apply_errors"] = apply_result.get("errors", [])
        else:
            result["dry_run"] = True
            result["message"] = "Preview only - set apply=true and dry_run=false to apply changes"
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[compose] Error: {error_msg}")
        print(f"[compose] Traceback:\n{error_trace}")
        return jsonify({"ok": False, "error": error_msg, "traceback": error_trace}), 500


@app.post("/generate_docs")
def generate_docs():
    """
    Documentation generation endpoint.
    Generates docstrings, README files, or API documentation for code.
    
    Accepts:
    - doc_type: Type of documentation ("docstring", "readme", "api") (required)
    - file_path: Path to file containing code (optional, required for docstring/api if code_snippet not provided)
    - code_snippet: Direct code snippet (optional, required for docstring/api if file_path not provided)
    - repo_dir: Repository directory (optional, for context and pattern matching)
    - doc_format: Documentation format (auto-detected if not provided)
      - For docstrings: "google", "numpy", "jsdoc", etc.
      - For README: "markdown"
      - For API: "markdown", "openapi", "json", etc.
    - target_name: Name of function/class for docstrings (optional)
    - model: Optional model override
    - max_tokens: Maximum tokens for generation (default: 4000 for README, 3000 otherwise)
    - stream: If true, stream the response (default: false)
    
    Returns:
    - If stream=false: Complete response with documentation, doc_type, doc_format, etc.
    - If stream=true: Server-Sent Events stream with chunks of documentation
    """
    try:
        data = request.json or {}
        doc_type = data.get("doc_type")
        file_path = data.get("file_path")
        code_snippet = data.get("code_snippet")
        repo_dir = data.get("repo_dir")
        doc_format = data.get("doc_format")
        target_name = data.get("target_name")
        model = data.get("model")
        # Use larger default for README generation (needs more context)
        default_max_tokens = 4000 if doc_type == "readme" else 3000
        max_tokens = int(data.get("max_tokens", default_max_tokens))
        
        # Validate input
        if not doc_type:
            return jsonify({"ok": False, "error": "doc_type is required (must be 'docstring', 'readme', or 'api')"}), 400
        
        if doc_type not in ["docstring", "readme", "api"]:
            return jsonify({"ok": False, "error": f"Invalid doc_type: {doc_type}. Must be 'docstring', 'readme', or 'api'"}), 400
        
        stream = data.get("stream", False)
        print(f"[generate_docs] Generating {doc_type} documentation (stream={stream})...")
        
        if stream:
            # Streaming response
            from backend.modules.documentation_generation import stream_generate_documentation
            
            def generate():
                try:
                    yield "data: " + json.dumps({"type": "start"}) + "\n\n"
                    
                    # Collect all chunks for metadata
                    doc_chunks = []
                    for chunk in stream_generate_documentation(
                        doc_type=doc_type,
                        file_path=file_path,
                        code_snippet=code_snippet,
                        repo_dir=repo_dir,
                        doc_format=doc_format,
                        target_name=target_name,
                        model=model,
                        max_tokens=max_tokens
                    ):
                        if chunk.startswith("Error:"):
                            yield "data: " + json.dumps({"type": "error", "error": chunk}) + "\n\n"
                            return
                        doc_chunks.append(chunk)
                        yield "data: " + json.dumps({"type": "chunk", "content": chunk}) + "\n\n"
                    
                    # Get metadata
                    documentation = "".join(doc_chunks)
                    
                    # Determine language and format
                    language = "markdown" if doc_type == "readme" else (doc_format or "default")
                    
                    yield "data: " + json.dumps({
                        "type": "done",
                        "doc_type": doc_type,
                        "doc_format": doc_format or "default",
                        "language": language,
                        "target_name": target_name,
                        "lines": len(documentation.splitlines())
                    }) + "\n\n"
                except Exception as e:
                    yield "data: " + json.dumps({"type": "error", "error": str(e)}) + "\n\n"
            
            return Response(stream_with_context(generate()), mimetype='text/event-stream')
        else:
            # Non-streaming response
            result = generate_documentation(
                doc_type=doc_type,
                file_path=file_path,
                code_snippet=code_snippet,
                repo_dir=repo_dir,
                doc_format=doc_format,
                target_name=target_name,
                model=model,
                max_tokens=max_tokens
            )
            
            if not result.get("ok"):
                return jsonify(result), 500
            
            return jsonify(result)
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[generate_docs] Error: {error_msg}")
        print(f"[generate_docs] Traceback:\n{error_trace}")
        return jsonify({"ok": False, "error": error_msg, "traceback": error_trace}), 500


@app.post("/edit")
def edit():
    """
    Direct code editing endpoint for editor-based AI editing.
    Edits selected code directly in the editor based on natural language instructions.
    
    Accepts:
    - selected_code: The code snippet to edit (required)
    - instruction: Natural language instruction for editing (required)
    - file_path: Path to the file containing the code (required)
    - repo_dir: Optional repository directory for codebase context
    - file_context: Optional surrounding code context (before/after selected code)
    - language: Optional programming language (auto-detected from file extension)
    - model: Optional model override
    - temperature: Temperature for LLM generation (default: 0.3)
    - stream: If true, stream the response (default: false)
    
    Returns:
    - If stream=false: Complete response with original_code, edited_code, diff, etc.
    - If stream=true: Server-Sent Events stream with chunks of edited code
    """
    try:
        data = request.json or {}
        selected_code = data.get("selected_code")
        instruction = data.get("instruction")
        file_path = data.get("file_path")
        repo_dir = data.get("repo_dir")
        file_context = data.get("file_context")
        language = data.get("language")
        model = data.get("model")
        temperature = float(data.get("temperature", 0.3))
        stream = data.get("stream", False)
        
        # Validate input
        if not selected_code:
            return jsonify({"ok": False, "error": "selected_code is required"}), 400
        
        if not instruction:
            return jsonify({"ok": False, "error": "instruction is required"}), 400
        
        if not file_path:
            return jsonify({"ok": False, "error": "file_path is required"}), 400
        
        print(f"[edit] Editing code in {Path(file_path).name} based on: {instruction[:80]}... (stream={stream})")
        
        if stream:
            # Streaming response
            from backend.modules.direct_edit import stream_edit_code_directly
            
            # Detect language once before the inner function (capture it)
            detected_language = language
            if not detected_language:
                file_ext = Path(file_path).suffix.lower()
                lang_map = {
                    '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                    '.tsx': 'typescript', '.jsx': 'javascript', '.java': 'java',
                    '.cpp': 'cpp', '.c': 'c', '.cs': 'csharp', '.go': 'go',
                    '.rs': 'rust', '.rb': 'ruby', '.php': 'php', '.swift': 'swift',
                    '.kt': 'kotlin', '.scala': 'scala', '.vue': 'vue',
                    '.html': 'html', '.css': 'css', '.sql': 'sql',
                    '.sh': 'bash', '.bat': 'batch', '.ps1': 'powershell'
                }
                detected_language = lang_map.get(file_ext, 'text')
            
            def generate():
                try:
                    yield "data: " + json.dumps({"type": "start"}) + "\n\n"
                    
                    # Collect all chunks for metadata
                    edited_code_chunks = []
                    for chunk in stream_edit_code_directly(
                        selected_code=selected_code,
                        instruction=instruction,
                        file_path=file_path,
                        repo_dir=repo_dir,
                        file_context=file_context,
                        language=detected_language,  # Use detected_language here
                        model=model,
                        temperature=temperature
                    ):
                        if chunk.startswith("Error:"):
                            yield "data: " + json.dumps({"type": "error", "error": chunk}) + "\n\n"
                            return
                        edited_code_chunks.append(chunk)
                        yield "data: " + json.dumps({"type": "chunk", "content": chunk}) + "\n\n"
                    
                    # Get metadata
                    edited_code = "".join(edited_code_chunks)
                    
                    # Clean up the response (remove markdown code blocks if present)
                    edited_code = edited_code.strip()
                    if "```" in edited_code:
                        import re
                        # Build regex pattern with language if available
                        lang_pattern = detected_language if detected_language else ''
                        pattern = rf'```{lang_pattern}?\s*\n(.*?)\n```' if lang_pattern else r'```\s*\n(.*?)\n```'
                        code_block_match = re.search(pattern, edited_code, re.DOTALL)
                        if code_block_match:
                            edited_code = code_block_match.group(1)
                        else:
                            # Try simpler pattern
                            lines = edited_code.splitlines()
                            if lines and lines[0].startswith('```'):
                                lines = lines[1:]
                            if lines and lines[-1].strip() == '```':
                                lines = lines[:-1]
                            edited_code = '\n'.join(lines)
                    
                    # Generate diff
                    diff_text = generate_diff_text(selected_code, edited_code, Path(file_path).name)
                    
                    # Calculate line changes
                    old_lines = selected_code.splitlines()
                    new_lines = edited_code.splitlines()
                    lines_added = len(new_lines) - len(old_lines)
                    lines_removed = max(0, len(old_lines) - len(new_lines)) if lines_added >= 0 else 0
                    
                    yield "data: " + json.dumps({
                        "type": "done",
                        "original_code": selected_code,
                        "edited_code": edited_code,
                        "file_path": file_path,
                        "language": detected_language,
                        "lines_added": lines_added,
                        "lines_removed": lines_removed,
                        "instruction": instruction
                    }) + "\n\n"
                except Exception as e:
                    yield "data: " + json.dumps({"type": "error", "error": str(e)}) + "\n\n"
            
            return Response(stream_with_context(generate()), mimetype='text/event-stream')
        else:
            # Non-streaming response
            result = edit_code_directly(
                selected_code=selected_code,
                instruction=instruction,
                file_path=file_path,
                repo_dir=repo_dir,
                file_context=file_context,
                language=language,
                model=model,
                temperature=temperature
            )
            
            if not result.get("ok"):
                return jsonify(result), 500
            
            return jsonify(result)
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[edit] Error: {error_msg}")
        print(f"[edit] Traceback:\n{error_trace}")
        return jsonify({"ok": False, "error": error_msg, "traceback": error_trace}), 500


@app.post("/review")
def review_endpoint():
    """
    Code review endpoint.
    Analyzes code for bugs, security vulnerabilities, performance issues, and code quality.
    
    Accepts:
    - code: The code to review (required)
    - file_path: Path to the file being reviewed (optional)
    - repo_dir: Root directory of the repository (optional, for context)
    - language: Programming language (optional, auto-detected from file_path)
    - review_type: Type of review (comprehensive, security, performance, quality, bugs) (default: comprehensive)
    - code_context: Additional context about the code (optional)
    - model: Optional model override
    - stream: Whether to stream response (default: false)
    
    Returns:
    - If stream=false: Complete response with review_report, bugs, security_issues, performance_issues, quality_issues, summary
    - If stream=true: Server-Sent Events stream with chunks of review report
    """
    try:
        data = request.json or {}
        code = data.get("code") or data.get("code_snippet")  # Support both
        file_path = data.get("file_path")
        repo_dir = data.get("repo_dir")
        language = data.get("language")
        review_type = data.get("review_type", "comprehensive")
        code_context = data.get("code_context")
        model = data.get("model")
        stream = data.get("stream", False)
        
        # Validate input
        if not code:
            return jsonify({"ok": False, "error": "code or code_snippet is required"}), 400
        
        # Auto-detect language from file_path if not provided
        if not language and file_path:
            file_ext = Path(file_path).suffix.lower()
            lang_map = {
                '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                '.tsx': 'typescript', '.jsx': 'javascript', '.java': 'java',
                '.cpp': 'cpp', '.c': 'c', '.cs': 'csharp', '.go': 'go',
                '.rs': 'rust', '.rb': 'ruby', '.php': 'php', '.swift': 'swift',
                '.kt': 'kotlin', '.scala': 'scala', '.vue': 'vue',
                '.html': 'html', '.css': 'css', '.sql': 'sql',
                '.sh': 'bash', '.bat': 'batch', '.ps1': 'powershell'
            }
            language = lang_map.get(file_ext, 'text')
        
        if not language:
            language = 'python'  # Default
        
        print(f"[review] Reviewing code ({review_type} review, language: {language}, stream={stream})...")
        
        if stream:
            # Streaming response
            def generate():
                try:
                    yield "data: " + json.dumps({"type": "start"}) + "\n\n"
                    
                    # Collect all chunks for metadata
                    review_chunks = []
                    for chunk_data in stream_review_code(
                        code=code,
                        language=language,
                        file_path=file_path,
                        repo_dir=repo_dir,
                        review_type=review_type,
                        code_context=code_context
                    ):
                        if chunk_data.startswith("data: "):
                            data_str = chunk_data[6:]
                            try:
                                data_obj = json.loads(data_str)
                                if data_obj.get("type") == "error":
                                    yield chunk_data
                                    return
                                elif data_obj.get("type") == "chunk":
                                    review_chunks.append(data_obj.get("content", ""))
                                    yield chunk_data
                                elif data_obj.get("type") == "done":
                                    yield chunk_data
                                    return
                            except:
                                pass
                        else:
                            # Handle old format (just strings)
                            review_chunks.append(chunk_data)
                            yield "data: " + json.dumps({"type": "chunk", "content": chunk_data}) + "\n\n"
                    
                    # Final done event if not already sent
                    review_report = "".join(review_chunks)
                    if review_report:
                        from backend.modules.code_review import parse_review_report
                        parsed_results = parse_review_report(review_report, file_path)
                        yield "data: " + json.dumps({
                            "type": "done",
                            "review_type": review_type,
                            "language": language,
                            "file_path": file_path,
                            **parsed_results
                        }) + "\n\n"
                except Exception as e:
                    error_msg = str(e)
                    error_trace = traceback.format_exc()
                    print(f"[review] Stream error: {error_msg}")
                    print(f"[review] Traceback:\n{error_trace}")
                    yield "data: " + json.dumps({"type": "error", "error": error_msg}) + "\n\n"
            
            return Response(stream_with_context(generate()), mimetype='text/event-stream')
        else:
            # Non-streaming response
            result = review_code(
                code=code,
                language=language,
                file_path=file_path,
                repo_dir=repo_dir,
                review_type=review_type,
                code_context=code_context
            )
            
            if not result.get("ok"):
                return jsonify(result), 500
            
            return jsonify(result)
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[review] Error: {error_msg}")
        print(f"[review] Traceback:\n{error_trace}")
        return jsonify({"ok": False, "error": error_msg, "traceback": error_trace}), 500


@app.post("/generate_tests")
@handle_errors()
def generate_tests_endpoint():
    """
    Test generation endpoint.
    Generates unit tests or integration tests for existing code.
    
    Accepts:
    - file_path: Path to file containing code to test (optional)
    - code_snippet: Direct code snippet to test (optional, required if file_path not provided)
    - repo_dir: Repository directory (optional, for context and framework detection)
    - test_framework: Testing framework to use (optional, auto-detected if not provided)
    - test_type: Type of tests ("unit" or "integration", default: "unit")
    - model: Optional model override
    - max_tokens: Maximum tokens for generation (default: 3000)
    - stream: Whether to stream response (default: false)
    
    Returns:
    - If stream=false: Complete response with test_code, test_framework, language, etc.
    - If stream=true: Server-Sent Events stream with chunks of test code
    """
    try:
        data = request.json or {}
        file_path = data.get("file_path")
        code_snippet = data.get("code_snippet")
        repo_dir = data.get("repo_dir")
        test_framework = data.get("test_framework")
        test_type = data.get("test_type", "unit")
        model = data.get("model")
        max_tokens = int(data.get("max_tokens", 3000))
        stream = data.get("stream", False)
        
        # Validate input
        if not file_path and not code_snippet:
            return jsonify({"ok": False, "error": "Either file_path or code_snippet is required"}), 400
        
        print(f"[generate_tests] Generating {test_type} tests (stream={stream})...")
        
        if stream:
            # Streaming response
            from backend.modules.test_generation import stream_generate_tests
            
            def generate():
                try:
                    # Get metadata first (need to determine language and framework)
                    # We'll do a quick non-streaming call for metadata, then stream the actual generation
                    # Actually, let's just stream and include metadata in the stream
                    yield "data: " + json.dumps({"type": "start"}) + "\n\n"
                    
                    # Collect all chunks for metadata
                    test_code_chunks = []
                    for chunk in stream_generate_tests(
                        file_path=file_path,
                        code_snippet=code_snippet,
                        repo_dir=repo_dir,
                        test_framework=test_framework,
                        test_type=test_type,
                        model=model,
                        max_tokens=max_tokens
                    ):
                        if chunk.startswith("Error:"):
                            yield "data: " + json.dumps({"type": "error", "error": chunk}) + "\n\n"
                            return
                        test_code_chunks.append(chunk)
                        yield "data: " + json.dumps({"type": "chunk", "content": chunk}) + "\n\n"
                    
                    # Get metadata
                    test_code = "".join(test_code_chunks)
                    # Determine test file name
                    test_file_name = None
                    if file_path:
                        file_name = Path(file_path).stem
                        # Detect language from file
                        ext = Path(file_path).suffix.lower()
                        if ext == '.py':
                            language = "python"
                        elif ext in ['.js', '.jsx']:
                            language = "javascript"
                        elif ext in ['.ts', '.tsx']:
                            language = "typescript"
                        else:
                            language = "python"  # default
                        
                        if language == "python":
                            test_file_name = f"test_{file_name}.py"
                        elif language in ["javascript", "typescript"]:
                            test_file_name = f"{file_name}.test{ext}"
                    
                    yield "data: " + json.dumps({
                        "type": "done",
                        "test_framework": test_framework or "default",
                        "language": language if file_path else "python",
                        "test_type": test_type,
                        "test_file_name": test_file_name,
                        "lines": len(test_code.splitlines())
                    }) + "\n\n"
                except Exception as e:
                    yield "data: " + json.dumps({"type": "error", "error": str(e)}) + "\n\n"
            
            return Response(stream_with_context(generate()), mimetype='text/event-stream')
        else:
            # Non-streaming response
            result = generate_tests(
                file_path=file_path,
                code_snippet=code_snippet,
                repo_dir=repo_dir,
                test_framework=test_framework,
                test_type=test_type,
                model=model,
                max_tokens=max_tokens
            )
            
            print(f"[generate_tests] Result: ok={result.get('ok')}, test_code length={len(result.get('test_code', '')) if result.get('test_code') else 0}")
            
            if not result.get("ok"):
                print(f"[generate_tests] Error in result: {result.get('error')}")
                return jsonify(result), 500
            
            return jsonify(result)
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[generate_tests] Error: {error_msg}")
        print(f"[generate_tests] Traceback:\n{error_trace}")
        return jsonify({"ok": False, "error": error_msg, "traceback": error_trace}), 500


@app.post("/answer")
def answer():
    """Legacy endpoint - kept for backward compatibility"""
    try:
        data = request.json
        question = data.get("question")
        evidences = data.get("evidences", [])
        
        if not question or not evidences:
            return jsonify({"ok": False, "error": "question and evidences are required"}), 400
        
        md = answer_with_citations(question, evidences)
        return jsonify({
            "ok": True,
            "markdown": md,
            "citations": [{"file": e["file"], "start": e["start"], "end": e["end"]} for e in evidences]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/cache/stats")
def cache_stats():
    """Get cache statistics for all caches."""
    try:
        from backend.modules.cache import get_all_cache_stats
        stats = get_all_cache_stats()
        
        return jsonify({
            "ok": True,
            "stats": stats,
            "summary": {
                "total_hits": stats["llm"]["hits"] + stats["search"]["hits"] + stats["embeddings"]["hits"],
                "total_misses": stats["llm"]["misses"] + stats["search"]["misses"] + stats["embeddings"]["misses"],
                "total_size_mb": stats["llm"]["total_size_mb"] + stats["search"]["total_size_mb"] + stats["embeddings"]["total_size_mb"],
                "total_entries": stats["llm"]["total_entries"] + stats["search"]["total_entries"] + stats["embeddings"]["total_entries"]
            }
        })
    except ImportError:
        return jsonify({
            "ok": False,
            "error": "Caching module not available"
        }), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/cache/clear")
def cache_clear():
    """
    Clear all caches or specific cache type.
    
    Accepts:
    - cache_type: Optional, one of "llm", "search", "embeddings", or "all" (default: "all")
    """
    try:
        from backend.modules.cache import (
            get_llm_cache, get_search_cache, get_embedding_cache,
            clear_all_caches
        )
        
        data = request.json or {}
        cache_type = data.get("cache_type", "all").lower()
        
        if cache_type == "all":
            cleared = clear_all_caches()
            return jsonify({
                "ok": True,
                "message": "All caches cleared",
                "cleared": cleared
            })
        elif cache_type == "llm":
            count = get_llm_cache(cache_dir=f"{DATA_DIR}/cache/llm").cache.clear()
            return jsonify({
                "ok": True,
                "message": "LLM cache cleared",
                "cleared": {"llm": count}
            })
        elif cache_type == "search":
            count = get_search_cache(cache_dir=f"{DATA_DIR}/cache/search").cache.clear()
            return jsonify({
                "ok": True,
                "message": "Search cache cleared",
                "cleared": {"search": count}
            })
        elif cache_type == "embeddings":
            count = get_embedding_cache(cache_dir=f"{DATA_DIR}/cache/embeddings").cache.clear()
            return jsonify({
                "ok": True,
                "message": "Embeddings cache cleared",
                "cleared": {"embeddings": count}
            })
        else:
            return jsonify({
                "ok": False,
                "error": f"Invalid cache_type: {cache_type}. Must be one of: llm, search, embeddings, all"
            }), 400
    
    except ImportError:
        return jsonify({
            "ok": False,
            "error": "Caching module not available"
        }), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/cache/cleanup")
def cache_cleanup():
    """Remove expired cache entries from all caches."""
    try:
        from backend.modules.cache import cleanup_all_caches
        cleaned = cleanup_all_caches()
        
        return jsonify({
            "ok": True,
            "message": "Expired cache entries removed",
            "cleaned": cleaned,
            "total_removed": sum(cleaned.values())
        })
    except ImportError:
        return jsonify({
            "ok": False,
            "error": "Caching module not available"
        }), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/privacy/status")
def privacy_status():
    """Get privacy mode status and statistics."""
    try:
        privacy_mode = get_privacy_mode()
        status = privacy_mode.get_status()
        
        return jsonify({
            "ok": True,
            **status
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/privacy/enable")
def privacy_enable():
    """Enable privacy mode (runtime)."""
    try:
        privacy_mode = get_privacy_mode()
        privacy_mode.enable()
        
        return jsonify({
            "ok": True,
            "message": "Privacy mode enabled",
            "enabled": True,
            "note": "No code will be stored in indexes or caches"
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/privacy/disable")
def privacy_disable():
    """Disable privacy mode (runtime)."""
    try:
        privacy_mode = get_privacy_mode()
        privacy_mode.disable()
        
        return jsonify({
            "ok": True,
            "message": "Privacy mode disabled",
            "enabled": False,
            "note": "Code will be indexed and cached normally"
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/privacy/clear")
def privacy_clear():
    """
    Clear all stored data (indexes, caches) when privacy mode is enabled.
    GDPR compliance - right to be forgotten.
    """
    try:
        privacy_mode = get_privacy_mode()
        result = privacy_mode.clear_all_data()
        
        if result.get("ok"):
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/generate_project")
@require_auth
@handle_errors()
def generate_project():
    """
    Generate complete full-stack project (frontend + backend + database).
    Designed for non-coders to build complete projects through natural language.
    
    Accepts:
    - description: Natural language description of the project (required)
      Example: "Build me a todo app with React frontend, Flask backend, and SQLite database"
    - repo_path: Path where project should be created (required)
    - preferred_languages: Optional preferred programming languages {"backend": "python", "frontend": "javascript", "database": "sqlite"}
      If not provided, will auto-detect from existing code in repo_path (if exists)
      If no existing code, defaults to python for backend, javascript for frontend
    - stack: Optional stack override {"frontend": "react", "backend": "flask", "database": "sqlite"}
    - features: Optional features list ["authentication", "CRUD"]
    - dry_run: If true, return preview without creating files (default: true)
    - apply: If true, create files (default: false, requires dry_run=false)
    - stream: If true, stream progress updates via SSE (default: false)
    
    Returns:
    - If stream=false: Complete response with project structure, files, dependencies, setup instructions
    - If stream=true: Server-Sent Events stream with progress updates and final result
    """
    try:
        data = request.json or {}
        description = data.get("description")
        repo_path = data.get("repo_path")
        stack = data.get("stack")
        features = data.get("features")
        dry_run = data.get("dry_run", True)
        apply_changes = data.get("apply", False)
        stream = data.get("stream", False)
        
        if not description:
            return jsonify({"ok": False, "error": "description is required"}), 400
        
        if not repo_path:
            return jsonify({"ok": False, "error": "repo_path is required"}), 400
        
        should_create = apply_changes and not dry_run
        
        print(f"[generate_project] Generating full-stack project: {description[:80]}...")
        print(f"[generate_project] Target path: {repo_path}")
        print(f"[generate_project] Dry run: {dry_run}, Apply: {apply_changes}, Stream: {stream}")
        
        if stream:
            # Streaming response using template-based approach
            from backend.modules.template_generator import generate_from_templates
            from backend.modules.full_stack_generator import detect_stack_from_description, extract_features
            from backend.modules.language_detector import detect_stack_from_directory
            
            # Detect stack if not provided
            if not stack:
                # Priority 1: User's preferred languages (if provided)
                if preferred_languages:
                    stack = {
                        "frontend": preferred_languages.get("frontend", "react"),
                        "backend": preferred_languages.get("backend", "flask"),
                        "database": preferred_languages.get("database", "sqlite")
                    }
                    # Map languages to frameworks
                    if stack["backend"] == "python":
                        stack["backend"] = "flask"
                    elif stack["backend"] == "nodejs":
                        stack["backend"] = "express"
                    elif stack["backend"] == "java":
                        stack["backend"] = "spring"
                    # Frontend already handled (react/vue/angular)
                
                # Priority 2: Detect from existing code
                elif os.path.exists(repo_path):
                    detected_stack = detect_stack_from_directory(repo_path)
                    
                    # If stack detected from code, use it
                    if any(detected_stack.values()):
                        stack = detected_stack
                    # Fill in defaults if missing
                    if not stack.get("frontend"):
                        stack["frontend"] = "react"  # Default
                    if not stack.get("backend"):
                        stack["backend"] = "flask"  # Default
                    if not stack.get("database"):
                        stack["database"] = "sqlite"  # Default
                
                # Priority 3: Detect from description
                else:
                    stack = detect_stack_from_description(description)
            else:
                # Ensure all stack components are set
                if "frontend" not in stack:
                    stack["frontend"] = "react"
                if "backend" not in stack:
                    stack["backend"] = "flask"
                if "database" not in stack:
                    stack["database"] = "sqlite"
            
            def generate():
                try:
                    yield "data: " + json.dumps({"type": "start"}) + "\n\n"
                    
                    # Collect all progress messages and results
                    progress_messages = []
                    result_data = None
                    
                    for progress in generate_from_templates(
                        description=description,
                        stack=stack,
                        repo_path=repo_path,
                        dry_run=not should_create
                    ):
                        if progress.startswith("Error:"):
                            yield "data: " + json.dumps({"type": "error", "error": progress[6:].strip()}) + "\n\n"
                            return
                        
                        if progress.startswith("Progress:"):
                            progress_messages.append(progress)
                            yield "data: " + json.dumps({"type": "progress", "message": progress.strip()}) + "\n\n"
                        elif progress.strip().startswith("{"):
                            # This is the final result JSON
                            try:
                                result_data = json.loads(progress.strip())
                            except:
                                pass
                        else:
                            # Other content
                            pass
                    
                    # Send final result
                    if result_data:
                        generated_files = result_data.get("generated_files", [])
                        failed_files = result_data.get("failed_files", [])
                        sub_questions = result_data.get("sub_questions", [])
                        
                        # Associate project with user if created
                        if not should_create and len(generated_files) > 0:
                            from backend.modules.multi_repo import repo_id_from_path
                            repo_id = repo_id_from_path(repo_path)
                            user_auth.add_user_repository(
                                user_id=user_id,
                                repo_id=repo_id,
                                repo_path=repo_path,
                                repo_name=repo_id
                            )
                        
                        yield "data: " + json.dumps({
                            "type": "done",
                            "ok": True,
                            "repo_path": repo_path,
                            "stack": stack,
                            "features": features or extract_features(description),
                            "summary": f"Generated {len(generated_files)} files from {len(sub_questions)} sub-questions",
                            "total_files": len(generated_files),
                            "failed_files": len(failed_files),
                            "sub_questions_count": len(sub_questions),
                            "dry_run": not should_create,
                            "user_id": user_id
                        }) + "\n\n"
                    else:
                        yield "data: " + json.dumps({"type": "error", "error": "No result data received"}) + "\n\n"
                        
                except Exception as e:
                    yield "data: " + json.dumps({"type": "error", "error": str(e)}) + "\n\n"
            
            return Response(stream_with_context(generate()), mimetype='text/event-stream')
        else:
            # Non-streaming response using template-based approach
            import time
            start_time = time.time()
            
            from backend.modules.template_generator import generate_from_templates
            from backend.modules.full_stack_generator import detect_stack_from_description, extract_features
            
            # Detect stack if not provided
            if not stack:
                stack = detect_stack_from_description(description)
            
            try:
                # Collect results from generator
                generated_files = []
                failed_files = []
                sub_questions = []
                progress_messages = []
                result_data = None
                
                for progress in generate_from_templates(
                    description=description,
                    stack=stack,
                    repo_path=repo_path,
                    dry_run=not should_create
                ):
                    if progress.startswith("Error:"):
                        return jsonify({"ok": False, "error": progress[6:].strip()}), 500
                    
                    if progress.startswith("Progress:"):
                        progress_messages.append(progress)
                    elif progress.strip().startswith("{"):
                        try:
                            result_data = json.loads(progress.strip())
                            generated_files = result_data.get("generated_files", [])
                            failed_files = result_data.get("failed_files", [])
                            sub_questions = result_data.get("sub_questions", [])
                        except:
                            pass
                
                elapsed = time.time() - start_time
                print(f"[generate_project] Generation completed in {elapsed:.2f} seconds")
                
                result = {
                    "ok": True,
                    "repo_path": repo_path,
                    "stack": stack,
                    "features": features or extract_features(description),
                    "summary": f"Generated {len(generated_files)} files from {len(sub_questions)} sub-questions",
                    "total_files": len(generated_files),
                    "failed_files": len(failed_files),
                    "sub_questions_count": len(sub_questions),
                    "files": generated_files,
                    "dry_run": not should_create
                }
                
                return jsonify(result)
            except Exception as gen_error:
                elapsed = time.time() - start_time
                print(f"[generate_project] Exception after {elapsed:.2f} seconds")
                print(f"[generate_project] Exception type: {type(gen_error).__name__}")
                print(f"[generate_project] Exception message: {str(gen_error)}")
                raise  # Let handle_errors decorator catch it
    
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[generate_project] Error: {error_msg}")
        print(f"[generate_project] Traceback:\n{error_trace}")
        return jsonify({"ok": False, "error": error_msg, "traceback": error_trace}), 500


# ============================================================================
# User Authentication Endpoints
# ============================================================================

@app.post("/auth/register")
@handle_errors()
def register():
    """
    Register a new user.
    
    Accepts:
    - username: Unique username (required, min 3 chars)
    - email: Unique email address (required)
    - password: Password (required, min 6 chars)
    
    Returns:
    - User data and success message
    """
    try:
        data = request.json or {}
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        
        if not username or not email or not password:
            return jsonify({"ok": False, "error": "username, email, and password are required"}), 400
        
        result = user_auth.register_user(username, email, password)
        
        if result.get("ok"):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/auth/login")
@handle_errors()
def login():
    """
    Login user and get JWT token.
    
    Accepts:
    - username_or_email: Username or email address (required)
    - password: Password (required)
    
    Returns:
    - JWT token and user data
    """
    try:
        data = request.json or {}
        username_or_email = data.get("username_or_email") or data.get("username") or data.get("email")
        password = data.get("password")
        
        if not username_or_email or not password:
            return jsonify({"ok": False, "error": "username/email and password are required"}), 400
        
        result = user_auth.login_user(username_or_email, password)
        
        if result.get("ok"):
            return jsonify(result), 200
        else:
            return jsonify(result), 401
    
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/auth/me")
@require_auth
@handle_errors()
def get_current_user():
    """
    Get current authenticated user information.
    Requires authentication.
    
    Returns:
    - Current user data
    """
    try:
        print(f"[auth/me] Endpoint called - User ID: {request.current_user_id}")
        user_id = request.current_user_id
        user = user_auth.get_user_by_id(user_id)
        
        if not user:
            print(f"[auth/me] ❌ User {user_id} not found in database")
            return jsonify({"ok": False, "error": "User not found"}), 404
        
        print(f"[auth/me] ✅ User found: {user.username} (ID: {user.id})")
        return jsonify({
            "ok": True,
            "user": user.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.put("/auth/me")
@require_auth
@handle_errors()
def update_current_user():
    """
    Update current user information.
    Requires authentication.
    
    Accepts:
    - email: New email (optional)
    - password: New password (optional)
    - username: New username (optional)
    - phone_number: New phone number in E.164 format (optional, e.g., +1234567890)
    
    Returns:
    - Updated user data
    """
    try:
        user_id = request.current_user_id
        data = request.json or {}
        
        result = user_auth.update_user(user_id, **data)
        
        if result.get("ok"):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.delete("/auth/me")
@require_auth
@handle_errors()
def delete_current_user():
    """
    Delete current user account.
    Requires authentication.
    
    Returns:
    - Success message
    """
    try:
        user_id = request.current_user_id
        result = user_auth.delete_user(user_id)
        
        if result.get("ok"):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/auth/forgot-password")
@handle_errors()
def forgot_password():
    """
    Request a password reset.
    
    Accepts:
    - email: User's email address
    
    Returns:
    - Success message (always returns success for security)
    - token: Reset token (development only - remove in production)
    """
    try:
        data = request.json or {}
        email = data.get("email")
        
        if not email:
            return jsonify({"ok": False, "error": "Email is required"}), 400
        
        result = user_auth.request_password_reset(email)
        
        # Log the result for debugging
        print(f"[forgot-password] Result: ok={result.get('ok')}, email_sent={result.get('email_sent')}, sms_sent={result.get('sms_sent')}")
        
        return jsonify(result), 200
    except Exception as e:
        print(f"[forgot-password] Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/auth/verify-reset-token")
@handle_errors()
def verify_reset_token():
    """
    Verify a password reset token.
    
    Query params:
    - token: Reset token string
    
    Returns:
    - Success status and user info if token is valid
    """
    try:
        token = request.args.get("token")
        
        if not token:
            return jsonify({"ok": False, "error": "Token is required"}), 400
        
        result = user_auth.verify_reset_token(token)
        
        if result["ok"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/auth/reset-password")
@handle_errors()
def reset_password():
    """
    Reset password using a reset token.
    
    Accepts:
    - token: Reset token string
    - password: New password (min 6 characters)
    
    Returns:
    - Success status
    """
    try:
        data = request.json or {}
        token = data.get("token")
        password = data.get("password")
        
        if not token:
            return jsonify({"ok": False, "error": "Token is required"}), 400
        
        if not password:
            return jsonify({"ok": False, "error": "Password is required"}), 400
        
        result = user_auth.reset_password(token, password)
        
        if result["ok"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ============================================================================
# Repository Generation Endpoints
# ============================================================================

@app.post("/generate_repo")
@handle_errors()
def generate_repo():
    """
    Generate entire repository from scratch based on natural language description.
    Similar to Cursor's repository generation feature.
    
    Accepts:
    - description: Natural language description of the project to generate (required)
    - repo_path: Path where repository should be created (required)
    - project_type: Project type (optional, auto-detected if not provided)
      Examples: "nextjs", "react", "python", "flask", "express"
    - language: Primary programming language (optional, auto-detected if not provided)
      Examples: "python", "javascript", "typescript"
    - dry_run: If true, return preview without creating files (default: true)
    - apply: If true, create files (default: false, requires dry_run=false)
    - model: Optional model override
    - max_tokens: Maximum tokens for generation (default: 8000)
    
    Returns:
    - If dry_run=true: Preview of what would be created (no files created)
    - If apply=true: Results of creating the repository
    - Includes: file list, directories, summary, dependencies, setup instructions
    """
    try:
        data = request.json or {}
        description = data.get("description")
        repo_path = data.get("repo_path")
        project_type = data.get("project_type")
        language = data.get("language")
        dry_run = data.get("dry_run", True)  # Default to preview only
        apply_changes = data.get("apply", False)  # Default to false
        model = data.get("model")
        max_tokens = int(data.get("max_tokens", 8000))
        
        # Validate input
        if not description:
            return jsonify({"ok": False, "error": "description is required"}), 400
        
        if not repo_path:
            return jsonify({"ok": False, "error": "repo_path is required"}), 400
        
        # Determine if we should actually create files
        should_create = apply_changes and not dry_run
        
        print(f"[generate_repo] Generating repository: {description[:80]}...")
        print(f"[generate_repo] Target path: {repo_path}")
        print(f"[generate_repo] Dry run: {dry_run}, Apply: {apply_changes}")
        
        # Generate repository
        result = generate_repository(
            description=description,
            repo_path=repo_path,
            project_type=project_type,
            language=language,
            model=model,
            dry_run=not should_create,  # Create files if apply=true and dry_run=false
            temperature=0.3,
            max_tokens=max_tokens
        )
        
        if not result.get("ok"):
            return jsonify(result), 500
        
        # Associate repository with user if created
        if should_create:
            from backend.modules.multi_repo import repo_id_from_path
            repo_id = repo_id_from_path(repo_path)
            user_auth.add_user_repository(
                user_id=user_id,
                repo_id=repo_id,
                repo_path=repo_path,
                repo_name=repo_id
            )
            result["user_id"] = user_id
        
        return jsonify(result)
    
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[generate_repo] Error: {error_msg}")
        print(f"[generate_repo] Traceback:\n{error_trace}")
        return jsonify({"ok": False, "error": error_msg, "traceback": error_trace}), 500


# Cleanup function for graceful shutdown
import atexit
def cleanup():
    """Stop all watchers on shutdown."""
    try:
        sync_manager = get_sync_manager()
        sync_manager.stop_all()
    except:
        pass

def cleanup_privacy_mode():
    """Cleanup in-memory data on shutdown if privacy mode is enabled."""
    try:
        privacy_mode = get_privacy_mode()
        if privacy_mode.is_enabled():
            print("[privacy] Server shutting down - clearing in-memory data...")
            result = privacy_mode.clear_all_data()
            if result.get("ok"):
                print(f"[privacy] Cleared {result.get('indexes_cleared', 0)} indexes and {result.get('caches_cleared', 0)} caches")
    except Exception as e:
        print(f"[privacy] Error during cleanup: {e}")

atexit.register(cleanup)
atexit.register(cleanup_privacy_mode)

# App is run via backend/__main__.py when using: python -m backend.app
# Or can be run directly with proper PYTHONPATH: PYTHONPATH=. python backend/app.py
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)

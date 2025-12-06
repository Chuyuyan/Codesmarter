"""
Full-stack project generator for non-coders.
Generates complete projects with frontend, backend, and database all connected.
Uses multi-step generation to work around API timeout limitations.
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
import re

from backend.modules.llm_api import get_fresh_client
from backend.config import LLM_PROVIDER, LLM_MODEL


# Step 1: Generate project structure (simplified for speed)
STRUCTURE_PROMPT = """Generate project structure for: {description}

Stack: {frontend} frontend, {backend} backend, {database} database
Features: {features}

Return JSON only:
{{
  "project_structure": [
    {{"path": "frontend/src/App.js", "description": "Main component"}},
    {{"path": "backend/app.py", "description": "Flask app"}}
  ],
  "frontend_dependencies": ["react"],
  "backend_dependencies": ["flask"],
  "api_endpoints": [{{"method": "GET", "path": "/api/todos"}}],
  "database_tables": [{{"name": "todos", "columns": ["id", "title"]}}],
  "summary": "Todo app"
}}"""


# Step 2: Generate individual file content
FILE_GENERATION_PROMPT = """You are an expert full-stack developer. Generate the content for this file:

File Path: {file_path}
File Description: {file_description}
Project Context: {project_context}

Other files in project:
{other_files}

Generate the COMPLETE file content. Include:
- All necessary imports
- Complete implementation
- Proper error handling
- Comments where helpful

Return ONLY the file content, no markdown code blocks, no explanations, just the raw file content."""


def detect_stack_from_description(description: str) -> Dict[str, str]:
    """
    Detect frontend, backend, and database stack from description.
    
    Returns:
        Dictionary with frontend, backend, database
    """
    description_lower = description.lower()
    
    # Frontend detection
    frontend = "react"  # Default
    if any(kw in description_lower for kw in ["vue", "vue.js", "vuejs"]):
        frontend = "vue"
    elif any(kw in description_lower for kw in ["angular"]):
        frontend = "angular"
    elif any(kw in description_lower for kw in ["next.js", "nextjs", "next js"]):
        frontend = "nextjs"
    elif any(kw in description_lower for kw in ["html", "vanilla", "plain javascript"]):
        frontend = "html"
    
    # Backend detection
    backend = "flask"  # Default
    if any(kw in description_lower for kw in ["express", "express.js", "node.js", "nodejs"]):
        backend = "express"
    elif any(kw in description_lower for kw in ["django"]):
        backend = "django"
    elif any(kw in description_lower for kw in ["fastapi"]):
        backend = "fastapi"
    elif any(kw in description_lower for kw in ["spring", "java"]):
        backend = "spring"
    
    # Database detection
    database = "sqlite"  # Default
    if any(kw in description_lower for kw in ["postgresql", "postgres", "pg"]):
        database = "postgresql"
    elif any(kw in description_lower for kw in ["mysql"]):
        database = "mysql"
    elif any(kw in description_lower for kw in ["mongodb", "mongo"]):
        database = "mongodb"
    elif any(kw in description_lower for kw in ["sqlite"]):
        database = "sqlite"
    
    return {
        "frontend": frontend,
        "backend": backend,
        "database": database
    }


def extract_features(description: str) -> List[str]:
    """
    Extract features from user description.
    
    Returns:
        List of detected features
    """
    description_lower = description.lower()
    features = []
    
    # Common features
    feature_keywords = {
        "authentication": ["auth", "login", "register", "sign in", "sign up", "authentication"],
        "crud": ["crud", "create", "read", "update", "delete", "manage"],
        "todo": ["todo", "task", "tasks"],
        "blog": ["blog", "post", "posts", "article", "articles"],
        "ecommerce": ["shop", "store", "cart", "checkout", "payment", "ecommerce"],
        "chat": ["chat", "message", "messaging", "real-time"],
        "dashboard": ["dashboard", "admin", "analytics"],
        "api": ["api", "rest", "endpoint", "endpoints"]
    }
    
    for feature, keywords in feature_keywords.items():
        if any(kw in description_lower for kw in keywords):
            features.append(feature)
    
    # If no specific features, default to CRUD
    if not features:
        features = ["crud"]
    
    return features


def generate_project_structure(
    description: str,
    stack: Dict[str, str],
    features: List[str]
) -> Dict:
    """
    Step 1: Generate project structure (list of files, dependencies, etc.)
    This is a small API call that should complete quickly.
    """
    client = get_fresh_client()
    
    prompt = STRUCTURE_PROMPT.format(
        description=description,
        frontend=stack["frontend"],
        backend=stack["backend"],
        database=stack["database"],
        features=", ".join(features)
    )
    
    print(f"[full_stack_generator] Step 1: Generating project structure...")
    print(f"[full_stack_generator] Prompt length: {len(prompt)} characters")
    
    import time
    start_time = time.time()
    
    try:
        # Use streaming to start receiving tokens immediately
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,  # Very small - must complete quickly
            stream=True  # Use streaming to avoid timeout
        )
        
        # Collect streaming response
        response_text = ""
        for chunk in response:
            if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    response_text += delta.content
        
        elapsed = time.time() - start_time
        print(f"[full_stack_generator] Step 1 completed in {elapsed:.2f} seconds")
        
        response_text = response_text.strip()
        
        # Extract JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        structure_data = json.loads(response_text)
        return {
            "ok": True,
            "structure": structure_data
        }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[full_stack_generator] Step 1 failed after {elapsed:.2f} seconds: {e}")
        return {
            "ok": False,
            "error": f"Failed to generate project structure: {str(e)}"
        }


def generate_file_content(
    file_path: str,
    file_description: str,
    project_context: Dict,
    other_files: List[Dict]
) -> Dict:
    """
    Step 2: Generate content for a single file.
    This is a small API call per file.
    """
    client = get_fresh_client()
    
    # Build context about other files
    other_files_str = "\n".join([
        f"- {f.get('path', '')}: {f.get('description', '')}"
        for f in other_files[:10]  # Limit to first 10 to keep prompt small
    ])
    
    prompt = FILE_GENERATION_PROMPT.format(
        file_path=file_path,
        file_description=file_description,
        project_context=json.dumps(project_context, indent=2),
        other_files=other_files_str
    )
    
    import time
    start_time = time.time()
    
    try:
        # Use streaming to start receiving tokens immediately
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1200,  # Per file, reduced to ensure completion within timeout
            stream=True  # Use streaming to avoid timeout
        )
        
        # Collect streaming response
        content = ""
        for chunk in response:
            if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    content += delta.content
        
        elapsed = time.time() - start_time
        print(f"[full_stack_generator] Generated {file_path} in {elapsed:.2f} seconds")
        
        content = content.strip()
        
        # Remove markdown code blocks if present
        if "```" in content:
            # Extract content from code block
            lines = content.split("\n")
            if lines[0].startswith("```"):
                # Remove first line (```language)
                content = "\n".join(lines[1:])
            if content.endswith("```"):
                content = content[:-3].strip()
        
        return {
            "ok": True,
            "content": content
        }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[full_stack_generator] Failed to generate {file_path} after {elapsed:.2f} seconds: {e}")
        return {
            "ok": False,
            "error": f"Failed to generate {file_path}: {str(e)}"
        }


def stream_generate_full_stack_project(
    description: str,
    repo_path: str,
    stack: Optional[Dict[str, str]] = None,
    features: Optional[List[str]] = None,
    dry_run: bool = False
):
    """
    Stream full-stack project generation with multi-step approach.
    
    Yields progress updates as strings that can be sent via SSE.
    """
    import time
    
    try:
        # Step 0: Detect stack and features
        yield f"Progress: Detecting project stack...\n"
        if not stack:
            stack = detect_stack_from_description(description)
        yield f"Progress: Detected stack - Frontend: {stack['frontend']}, Backend: {stack['backend']}, Database: {stack['database']}\n"
        
        yield f"Progress: Extracting features...\n"
        if not features:
            features = extract_features(description)
        yield f"Progress: Features: {', '.join(features)}\n"
        
        # Step 1: Generate project structure
        yield f"Progress: Generating project structure (Step 1/2)...\n"
        structure_result = generate_project_structure(description, stack, features)
        
        if not structure_result.get("ok"):
            yield f"Error: {structure_result.get('error', 'Unknown error')}\n"
            return
        
        structure_data = structure_result["structure"]
        project_files = structure_data.get("project_structure", [])
        
        yield f"Progress: Project structure generated - {len(project_files)} files to create\n"
        
        # Build project context
        project_context = {
            "description": description,
            "stack": stack,
            "features": features,
            "dependencies": {
                "frontend": structure_data.get("frontend_dependencies", []),
                "backend": structure_data.get("backend_dependencies", [])
            },
            "api_endpoints": structure_data.get("api_endpoints", []),
            "database_tables": structure_data.get("database_tables", [])
        }
        
        # Step 2: Generate each file individually
        yield f"Progress: Generating file contents (Step 2/2)...\n"
        
        generated_files = []
        failed_files = []
        
        for i, file_info in enumerate(project_files):
            file_path = file_info.get("path", "")
            file_description = file_info.get("description", "")
            
            yield f"Progress: Generating file {i+1}/{len(project_files)}: {file_path}\n"
            
            # Generate file content
            file_result = generate_file_content(
                file_path=file_path,
                file_description=file_description,
                project_context=project_context,
                other_files=project_files
            )
            
            if file_result.get("ok"):
                generated_files.append({
                    "path": file_path,
                    "content": file_result["content"],
                    "description": file_description
                })
                yield f"Progress: ✓ Generated {file_path}\n"
            else:
                failed_files.append({
                    "path": file_path,
                    "error": file_result.get("error", "Unknown error")
                })
                yield f"Progress: ✗ Failed to generate {file_path}: {file_result.get('error')}\n"
        
        yield f"Progress: Generated {len(generated_files)}/{len(project_files)} files successfully\n"
        
        # Step 3: Create files (if not dry run)
        if not dry_run:
            yield f"Progress: Creating project files...\n"
            repo_path_obj = Path(repo_path)
            repo_path_obj.mkdir(parents=True, exist_ok=True)
            
            for i, file_info in enumerate(generated_files):
                file_path = repo_path_obj / file_info["path"]
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_info["content"])
                
                yield f"Progress: Created {i+1}/{len(generated_files)} files: {file_info['path']}\n"
            
            yield f"Progress: All files created successfully!\n"
        else:
            yield f"Progress: Dry run mode - files not created\n"
        
        yield f"Progress: Generation complete!\n"
        
        # Store results for final response
        yield json.dumps({
            "type": "result",
            "generated_files": generated_files,
            "failed_files": failed_files,
            "structure": structure_data
        }) + "\n"
        
    except Exception as e:
        yield f"Error: {str(e)}\n"


def generate_full_stack_project(
    description: str,
    repo_path: str,
    stack: Optional[Dict[str, str]] = None,
    features: Optional[List[str]] = None,
    dry_run: bool = False
) -> Dict:
    """
    Generate a complete full-stack project using multi-step approach.
    
    Args:
        description: User's project description
        repo_path: Where to create the project
        stack: Optional stack override (frontend, backend, database)
        features: Optional features list
        dry_run: If True, don't create files, just return structure
    
    Returns:
        Dictionary with project structure, files, and setup instructions
    """
    import time
    total_start = time.time()
    
    # Detect stack if not provided
    if not stack:
        stack = detect_stack_from_description(description)
    
    # Extract features if not provided
    if not features:
        features = extract_features(description)
    
    print(f"[full_stack_generator] Detected stack: {stack}")
    print(f"[full_stack_generator] Detected features: {features}")
    
    # Step 1: Generate project structure
    print(f"[full_stack_generator] Step 1: Generating project structure...")
    structure_result = generate_project_structure(description, stack, features)
    
    if not structure_result.get("ok"):
        return {
            "ok": False,
            "error": structure_result.get("error", "Failed to generate project structure")
        }
    
    structure_data = structure_result["structure"]
    project_files = structure_data.get("project_structure", [])
    
    print(f"[full_stack_generator] Step 1 complete: {len(project_files)} files to generate")
    
    # Build project context
    project_context = {
        "description": description,
        "stack": stack,
        "features": features,
        "dependencies": {
            "frontend": structure_data.get("frontend_dependencies", []),
            "backend": structure_data.get("backend_dependencies", [])
        },
        "api_endpoints": structure_data.get("api_endpoints", []),
        "database_tables": structure_data.get("database_tables", [])
    }
    
    # Step 2: Generate each file individually
    print(f"[full_stack_generator] Step 2: Generating {len(project_files)} files...")
    
    generated_files = []
    failed_files = []
    
    for i, file_info in enumerate(project_files):
        file_path = file_info.get("path", "")
        file_description = file_info.get("description", "")
        
        print(f"[full_stack_generator] Generating file {i+1}/{len(project_files)}: {file_path}")
        
        file_result = generate_file_content(
            file_path=file_path,
            file_description=file_description,
            project_context=project_context,
            other_files=project_files
        )
        
        if file_result.get("ok"):
            generated_files.append({
                "path": file_path,
                "content": file_result["content"],
                "description": file_description,
                "size": len(file_result["content"]),
                "lines": len(file_result["content"].split('\n'))
            })
        else:
            failed_files.append({
                "path": file_path,
                "error": file_result.get("error", "Unknown error")
            })
    
    print(f"[full_stack_generator] Step 2 complete: {len(generated_files)}/{len(project_files)} files generated")
    
    if failed_files:
        print(f"[full_stack_generator] Warning: {len(failed_files)} files failed to generate")
    
    # Step 3: Create files (if not dry run)
    created_files = []
    if not dry_run:
        repo_path_obj = Path(repo_path)
        repo_path_obj.mkdir(parents=True, exist_ok=True)
        
        for file_info in generated_files:
            file_path = repo_path_obj / file_info["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_info["content"])
            
            created_files.append({
                "path": file_info["path"],
                "size": file_info["size"],
                "lines": file_info["lines"]
            })
        
        print(f"[full_stack_generator] Created {len(created_files)} files")
    
    total_elapsed = time.time() - total_start
    print(f"[full_stack_generator] Total generation time: {total_elapsed:.2f} seconds")
    
    return {
        "ok": True,
        "repo_path": repo_path,
        "stack": stack,
        "features": features,
        "summary": structure_data.get("summary", ""),
        "frontend_dependencies": structure_data.get("frontend_dependencies", []),
        "backend_dependencies": structure_data.get("backend_dependencies", []),
        "api_endpoints": structure_data.get("api_endpoints", []),
        "database_tables": structure_data.get("database_tables", []),
        "files": generated_files,
        "failed_files": failed_files,
        "total_files": len(generated_files),
        "dry_run": dry_run
    }

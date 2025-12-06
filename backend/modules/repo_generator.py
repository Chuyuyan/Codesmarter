"""
Repository generation module - generates entire repositories from scratch.
Similar to Cursor's repository generation feature.
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
import os
import re

from backend.modules.llm_api import get_fresh_client
from backend.modules.code_generation import generate_code, get_language_from_file
from backend.config import LLM_PROVIDER, LLM_MODEL, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, DATA_DIR
import os


REPO_GENERATION_PROMPT = """You are an expert project generator. Generate a complete project structure from scratch based on the user's description.

The user wants to create: {description}

Generate a complete project structure including:
1. All necessary files (source code, config files, README, etc.)
2. Proper directory structure
3. Configuration files (package.json, requirements.txt, tsconfig.json, etc.)
4. README.md with setup instructions
5. .gitignore file (if applicable)
6. All dependencies and imports

Project Type: {project_type}
Primary Language: {language}

IMPORTANT: Return a JSON object with this exact structure:
{{
  "project_structure": [
    {{
      "path": "relative/file/path.ext",
      "content": "file content here",
      "type": "file"
    }},
    {{
      "path": "directory/",
      "type": "directory"
    }}
  ],
  "files": [
    {{
      "path": "relative/file/path.ext",
      "content": "complete file content",
      "language": "python|javascript|typescript|etc",
      "description": "what this file does"
    }}
  ],
  "summary": "Brief summary of what was generated",
  "dependencies": ["package1", "package2"],
  "setup_instructions": "How to set up and run this project"
}}

Return ONLY the JSON, no markdown, no explanations, just valid JSON."""


def detect_project_type(description: str) -> Tuple[str, str]:
    """
    Detect project type and primary language from description.
    
    Returns:
        Tuple of (project_type, language)
    """
    description_lower = description.lower()
    
    # Detect project types
    if any(keyword in description_lower for keyword in ["next.js", "nextjs", "next js"]):
        return "nextjs", "typescript"
    elif any(keyword in description_lower for keyword in ["react", "react app", "react application"]):
        return "react", "javascript"
    elif any(keyword in description_lower for keyword in ["vue", "vue.js"]):
        return "vue", "javascript"
    elif any(keyword in description_lower for keyword in ["angular"]):
        return "angular", "typescript"
    elif any(keyword in description_lower for keyword in ["django", "django app"]):
        return "django", "python"
    elif any(keyword in description_lower for keyword in ["flask", "flask app"]):
        return "flask", "python"
    elif any(keyword in description_lower for keyword in ["express", "express.js", "node.js", "nodejs"]):
        return "express", "javascript"
    elif any(keyword in description_lower for keyword in ["python", "python app", "python script"]):
        return "python", "python"
    elif any(keyword in description_lower for keyword in ["typescript", "ts"]):
        return "typescript", "typescript"
    elif any(keyword in description_lower for keyword in ["javascript", "js"]):
        return "javascript", "javascript"
    else:
        # Default: try to detect from other keywords
        if any(keyword in description_lower for keyword in ["web", "website", "web app"]):
            return "web", "javascript"
        elif any(keyword in description_lower for keyword in ["api", "rest api", "backend"]):
            return "api", "python"
        else:
            return "generic", "python"


def get_default_project_structure(project_type: str, language: str) -> List[Dict]:
    """
    Get default project structure templates for common project types.
    
    Returns:
        List of file/directory dictionaries
    """
    structures = {
        "nextjs": [
            {"path": "pages/", "type": "directory"},
            {"path": "components/", "type": "directory"},
            {"path": "public/", "type": "directory"},
            {"path": "styles/", "type": "directory"},
            {"path": "package.json", "type": "file", "priority": "high"},
            {"path": "tsconfig.json", "type": "file", "priority": "high"},
            {"path": "next.config.js", "type": "file"},
            {"path": "README.md", "type": "file", "priority": "high"},
            {"path": ".gitignore", "type": "file"}
        ],
        "react": [
            {"path": "src/", "type": "directory"},
            {"path": "src/components/", "type": "directory"},
            {"path": "public/", "type": "directory"},
            {"path": "package.json", "type": "file", "priority": "high"},
            {"path": "README.md", "type": "file", "priority": "high"},
            {"path": ".gitignore", "type": "file"}
        ],
        "python": [
            {"path": "src/", "type": "directory"},
            {"path": "tests/", "type": "directory"},
            {"path": "requirements.txt", "type": "file", "priority": "high"},
            {"path": "README.md", "type": "file", "priority": "high"},
            {"path": ".gitignore", "type": "file"},
            {"path": "setup.py", "type": "file"}
        ],
        "flask": [
            {"path": "app/", "type": "directory"},
            {"path": "app/__init__.py", "type": "file"},
            {"path": "app/routes.py", "type": "file"},
            {"path": "templates/", "type": "directory"},
            {"path": "static/", "type": "directory"},
            {"path": "requirements.txt", "type": "file", "priority": "high"},
            {"path": "README.md", "type": "file", "priority": "high"},
            {"path": ".gitignore", "type": "file"}
        ],
        "express": [
            {"path": "src/", "type": "directory"},
            {"path": "src/routes/", "type": "directory"},
            {"path": "src/controllers/", "type": "directory"},
            {"path": "package.json", "type": "file", "priority": "high"},
            {"path": "README.md", "type": "file", "priority": "high"},
            {"path": ".gitignore", "type": "file"}
        ]
    }
    
    return structures.get(project_type, [
        {"path": "src/", "type": "directory"},
        {"path": "README.md", "type": "file", "priority": "high"},
        {"path": ".gitignore", "type": "file"}
    ])


def generate_repository_structure(
    description: str,
    project_type: Optional[str] = None,
    language: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 8000
) -> Dict:
    """
    Generate complete repository structure from description.
    
    Args:
        description: Natural language description of the project
        project_type: Project type (auto-detected if None)
        language: Primary language (auto-detected if None)
        model: Optional model override
        temperature: Temperature for LLM generation
        max_tokens: Maximum tokens for generation
    
    Returns:
        Dict with project structure, files, and metadata
    """
    try:
        # Auto-detect project type and language if not provided
        if not project_type or not language:
            detected_type, detected_lang = detect_project_type(description)
            project_type = project_type or detected_type
            language = language or detected_lang
        
        print(f"[repo_generator] Project type: {project_type}, Language: {language}")
        
        # Model selection
        if model:
            model_to_use = model
        elif os.getenv("LLM_MODEL"):
            model_to_use = os.getenv("LLM_MODEL")
        elif LLM_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY and os.getenv("OPENAI_MODEL"):
            model_to_use = os.getenv("OPENAI_MODEL")
        else:
            model_to_use = LLM_MODEL
        
        # Build prompt
        prompt = REPO_GENERATION_PROMPT.format(
            description=description,
            project_type=project_type,
            language=language
        )
        
        print(f"[repo_generator] Generating repository structure...")
        
        # Generate using LLM
        # Handle Anthropic separately
        if LLM_PROVIDER == "anthropic":
            try:
                from anthropic import Anthropic
                anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
                message = anthropic_client.messages.create(
                    model=model_to_use,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = message.content[0].text
            except Exception as e:
                raise Exception(f"Anthropic API error: {str(e)}")
        else:
            # OpenAI-compatible providers
            api_client = get_fresh_client()
            rsp = api_client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=180  # 3 minute timeout for repo generation
            )
            response_text = rsp.choices[0].message.content
        
        # Parse JSON response
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines)
        
        # Try to extract JSON if wrapped in text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        try:
            structure_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"[repo_generator] Failed to parse JSON: {e}")
            print(f"[repo_generator] Response: {response_text[:500]}...")
            # Fallback: create minimal structure
            return {
                "ok": False,
                "error": f"Failed to parse LLM response as JSON: {str(e)}",
                "raw_response": response_text[:500]
            }
        
        # Validate structure
        if "files" not in structure_data:
            structure_data["files"] = []
        if "project_structure" not in structure_data:
            structure_data["project_structure"] = []
        
        return {
            "ok": True,
            "project_type": project_type,
            "language": language,
            **structure_data
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"[repo_generator] Error generating repository structure: {e}")
        return {
            "ok": False,
            "error": error_msg
        }


def create_repository_files(
    structure_data: Dict,
    repo_path: str,
    dry_run: bool = True
) -> Dict:
    """
    Create repository files from structure data.
    
    Args:
        structure_data: Structure data from generate_repository_structure
        repo_path: Path where repository should be created
        dry_run: If True, don't actually create files (just validate)
    
    Returns:
        Dict with results of file creation
    """
    try:
        repo_path_obj = Path(repo_path)
        
        if not structure_data.get("ok"):
            return structure_data
        
        files_data = structure_data.get("files", [])
        project_structure = structure_data.get("project_structure", [])
        
        results = {
            "created": [],
            "directories": [],
            "errors": [],
            "total_files": 0,
            "total_directories": 0
        }
        
        # First, create all directories
        all_dirs = set()
        
        # Add directories from project_structure
        for item in project_structure:
            if item.get("type") == "directory":
                dir_path = item.get("path", "")
                if dir_path:
                    all_dirs.add(dir_path)
        
        # Extract directories from file paths
        for file_data in files_data:
            file_path = file_data.get("path", "")
            if file_path:
                parent_dir = str(Path(file_path).parent)
                if parent_dir and parent_dir != ".":
                    all_dirs.add(parent_dir)
        
        # Create directories
        for dir_path in sorted(all_dirs):
            full_dir_path = repo_path_obj / dir_path
            try:
                if not dry_run:
                    full_dir_path.mkdir(parents=True, exist_ok=True)
                results["directories"].append(dir_path)
                results["total_directories"] += 1
            except Exception as e:
                error_msg = f"Error creating directory {dir_path}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"[repo_generator] {error_msg}")
        
        # Then, create all files
        for file_data in files_data:
            file_path = file_data.get("path", "")
            file_content = file_data.get("content", "")
            
            if not file_path:
                continue
            
            try:
                full_file_path = repo_path_obj / file_path
                
                # Ensure parent directory exists
                full_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                if not dry_run:
                    full_file_path.write_text(file_content, encoding="utf-8")
                
                results["created"].append({
                    "path": file_path,
                    "size": len(file_content),
                    "lines": len(file_content.splitlines())
                })
                results["total_files"] += 1
            except Exception as e:
                error_msg = f"Error creating file {file_path}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"[repo_generator] {error_msg}")
        
        return {
            "ok": True,
            "dry_run": dry_run,
            **results,
            "summary": structure_data.get("summary", ""),
            "dependencies": structure_data.get("dependencies", []),
            "setup_instructions": structure_data.get("setup_instructions", "")
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"[repo_generator] Error creating repository files: {e}")
        return {
            "ok": False,
            "error": error_msg
        }


def generate_repository(
    description: str,
    repo_path: str,
    project_type: Optional[str] = None,
    language: Optional[str] = None,
    model: Optional[str] = None,
    dry_run: bool = True,
    temperature: float = 0.3,
    max_tokens: int = 8000
) -> Dict:
    """
    Complete repository generation - generates structure and creates files.
    
    Args:
        description: Natural language description of the project
        repo_path: Path where repository should be created
        project_type: Project type (auto-detected if None)
        language: Primary language (auto-detected if None)
        model: Optional model override
        dry_run: If True, don't actually create files (just preview)
        temperature: Temperature for LLM generation
        max_tokens: Maximum tokens for generation
    
    Returns:
        Dict with generation results and file list
    """
    try:
        repo_path_obj = Path(repo_path)
        
        # Check if repository already exists (and has files)
        if repo_path_obj.exists() and any(repo_path_obj.iterdir()):
            return {
                "ok": False,
                "error": f"Repository path already exists and is not empty: {repo_path}",
                "suggestion": "Choose a different path or delete the existing directory"
            }
        
        # Generate repository structure
        print(f"[repo_generator] Generating repository structure from description...")
        structure_data = generate_repository_structure(
            description=description,
            project_type=project_type,
            language=language,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if not structure_data.get("ok"):
            return structure_data
        
        # Create repository files
        print(f"[repo_generator] Creating repository files (dry_run={dry_run})...")
        creation_results = create_repository_files(
            structure_data=structure_data,
            repo_path=repo_path,
            dry_run=dry_run
        )
        
        if not creation_results.get("ok"):
            return creation_results
        
        # Combine results
        return {
            "ok": True,
            "repo_path": repo_path,
            "project_type": structure_data.get("project_type"),
            "language": structure_data.get("language"),
            "summary": structure_data.get("summary", ""),
            "dependencies": structure_data.get("dependencies", []),
            "setup_instructions": structure_data.get("setup_instructions", ""),
            "files": creation_results["created"],
            "directories": creation_results["directories"],
            "total_files": creation_results["total_files"],
            "total_directories": creation_results["total_directories"],
            "errors": creation_results.get("errors", []),
            "dry_run": dry_run
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"[repo_generator] Error generating repository: {e}")
        return {
            "ok": False,
            "error": error_msg
        }


"""
Template-based project generator using granular sub-questions.
This approach uses base templates + small LLM calls to customize them,
avoiding API timeouts while maintaining flexibility.
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
import re
import os

from backend.modules.llm_api import get_fresh_client
from backend.config import LLM_MODEL


# Base template paths
TEMPLATE_BASE = Path(__file__).parent.parent.parent / "templates"
FRONTEND_TEMPLATE = TEMPLATE_BASE / "frontend" / "react-base"
BACKEND_TEMPLATE = TEMPLATE_BASE / "backend" / "flask-base"
DATABASE_TEMPLATE = TEMPLATE_BASE / "database" / "sqlite-base"
INTEGRATION_TEMPLATE = TEMPLATE_BASE / "integration" / "react-flask"


# Sub-question decomposition prompt
DECOMPOSE_PROMPT = """Break down this project request into granular sub-questions:

Project: {description}
Stack: {stack}

Each sub-question should be:
1. Small and specific (can be answered in <200 tokens)
2. Independent (can be answered separately)
3. Template-based (maps to a base template)

Return JSON only:
{{
  "sub_questions": [
    {{
      "question": "What components are needed for the todo list?",
      "template": "react-base",
      "target": "frontend/src/components/TodoList.jsx",
      "context": "todo list component"
    }},
    {{
      "question": "What API endpoints are needed for todos?",
      "template": "flask-base",
      "target": "backend/routes/todos.py",
      "context": "todo API routes"
    }}
  ],
  "dependencies": [
    {{"from": "database schema", "to": "backend models"}},
    {{"from": "backend routes", "to": "frontend API calls"}}
  ]
}}"""


# Template customization prompt
CUSTOMIZE_PROMPT = """Customize this template code for the specific requirement:

Template Code:
```{language}
{template_code}
```

Requirement: {requirement}
Context: {context}
Project: {project_description}

Replace placeholders ({{PLACEHOLDER}}) and customize the code.
Return ONLY the customized code, no markdown, no explanations."""


def load_template(template_name: str, file_path: str) -> Optional[str]:
    """
    Load a template file.
    
    Args:
        template_name: Name of template (react-base, flask-base, etc.)
        file_path: Relative path within template directory
    
    Returns:
        Template content or None if not found
    """
    template_map = {
        "react-base": FRONTEND_TEMPLATE,
        "flask-base": BACKEND_TEMPLATE,
        "sqlite-base": DATABASE_TEMPLATE,
        "react-flask": INTEGRATION_TEMPLATE
    }
    
    template_dir = template_map.get(template_name)
    if not template_dir or not template_dir.exists():
        return None
    
    full_path = template_dir / file_path
    if not full_path.exists():
        return None
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[template_generator] Error loading template {template_name}/{file_path}: {e}")
        return None


def find_template_files(template_name: str) -> List[str]:
    """
    Find all files in a template directory.
    
    Returns:
        List of relative file paths
    """
    template_map = {
        "react-base": FRONTEND_TEMPLATE,
        "flask-base": BACKEND_TEMPLATE,
        "sqlite-base": DATABASE_TEMPLATE,
        "react-flask": INTEGRATION_TEMPLATE
    }
    
    template_dir = template_map.get(template_name)
    if not template_dir or not template_dir.exists():
        return []
    
    files = []
    for root, dirs, filenames in os.walk(template_dir):
        # Skip hidden files and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for filename in filenames:
            if filename.startswith('.') or filename == '.gitkeep':
                continue
            
            rel_path = os.path.relpath(os.path.join(root, filename), template_dir)
            files.append(rel_path.replace('\\', '/'))  # Normalize path separators
    
    return files


def decompose_into_sub_questions(description: str, stack: Dict[str, str]) -> Dict:
    """
    Decompose project description into granular sub-questions.
    
    Returns:
        Dictionary with sub_questions and dependencies
    """
    client = get_fresh_client()
    
    prompt = DECOMPOSE_PROMPT.format(
        description=description,
        stack=json.dumps(stack, indent=2)
    )
    
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500,  # Small enough to avoid timeout
            stream=False
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Extract JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        return {
            "ok": True,
            "sub_questions": result.get("sub_questions", []),
            "dependencies": result.get("dependencies", [])
        }
    except Exception as e:
        print(f"[template_generator] Error decomposing: {e}")
        return {
            "ok": False,
            "error": str(e),
            "sub_questions": [],
            "dependencies": []
        }


def customize_template(
    template_code: str,
    requirement: str,
    context: str,
    project_description: str,
    language: str = "javascript"
) -> Dict:
    """
    Customize a template using a small LLM call.
    
    Returns:
        Dictionary with customized code
    """
    client = get_fresh_client()
    
    prompt = CUSTOMIZE_PROMPT.format(
        template_code=template_code,
        requirement=requirement,
        context=context,
        project_description=project_description,
        language=language
    )
    
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,  # Small per-file customization
            stream=False
        )
        
        customized_code = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if "```" in customized_code:
            lines = customized_code.split("\n")
            if lines[0].startswith("```"):
                customized_code = "\n".join(lines[1:])
            if customized_code.endswith("```"):
                customized_code = customized_code[:-3].strip()
        
        return {
            "ok": True,
            "code": customized_code
        }
    except Exception as e:
        print(f"[template_generator] Error customizing template: {e}")
        return {
            "ok": False,
            "error": str(e),
            "code": template_code  # Return original on error
        }


def detect_language_from_path(file_path: str) -> str:
    """Detect programming language from file path."""
    ext = Path(file_path).suffix.lower()
    lang_map = {
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".py": "python",
        ".sql": "sql",
        ".html": "html",
        ".css": "css",
        ".json": "json"
    }
    return lang_map.get(ext, "text")


def generate_from_templates(
    description: str,
    stack: Dict[str, str],
    repo_path: str,
    dry_run: bool = False
):
    """
    Generate project using template-based approach with granular sub-questions.
    
    Yields progress updates.
    """
    try:
        # Step 1: Decompose into sub-questions
        yield f"Progress: Decomposing project into sub-questions...\n"
        decomposition = decompose_into_sub_questions(description, stack)
        
        if not decomposition.get("ok"):
            yield f"Error: Failed to decompose project: {decomposition.get('error')}\n"
            return
        
        sub_questions = decomposition.get("sub_questions", [])
        yield f"Progress: Generated {len(sub_questions)} sub-questions\n"
        
        # Step 2: Process each sub-question
        generated_files = []
        failed_files = []
        
        for i, sq in enumerate(sub_questions):
            question = sq.get("question", "")
            template_name = sq.get("template", "")
            target_path = sq.get("target", "")
            context = sq.get("context", "")
            
            yield f"Progress: Processing sub-question {i+1}/{len(sub_questions)}: {question}\n"
            
            # Find matching template file
            template_files = find_template_files(template_name)
            if not template_files:
                yield f"Progress: ✗ No template files found for {template_name}\n"
                failed_files.append({
                    "path": target_path,
                    "error": f"Template {template_name} not found"
                })
                continue
            
            # For now, use the first matching file or a default
            # In a more sophisticated version, we'd match based on target_path
            template_file = template_files[0] if template_files else None
            
            # Load template
            template_code = load_template(template_name, template_file)
            if not template_code:
                yield f"Progress: ✗ Could not load template {template_name}/{template_file}\n"
                failed_files.append({
                    "path": target_path,
                    "error": f"Template file not found"
                })
                continue
            
            # Customize template
            language = detect_language_from_path(target_path)
            customize_result = customize_template(
                template_code=template_code,
                requirement=question,
                context=context,
                project_description=description,
                language=language
            )
            
            if customize_result.get("ok"):
                generated_files.append({
                    "path": target_path,
                    "content": customize_result["code"],
                    "template": template_name
                })
                yield f"Progress: ✓ Generated {target_path}\n"
            else:
                failed_files.append({
                    "path": target_path,
                    "error": customize_result.get("error", "Unknown error")
                })
                yield f"Progress: ✗ Failed to customize {target_path}\n"
        
        yield f"Progress: Generated {len(generated_files)}/{len(sub_questions)} files\n"
        
        # Step 3: Create files
        if not dry_run:
            yield f"Progress: Creating project files...\n"
            repo_path_obj = Path(repo_path)
            repo_path_obj.mkdir(parents=True, exist_ok=True)
            
            for file_info in generated_files:
                file_path = repo_path_obj / file_info["path"]
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_info["content"])
                
                yield f"Progress: Created {file_info['path']}\n"
        
        yield f"Progress: Generation complete!\n"
        
        # Final result
        yield json.dumps({
            "type": "result",
            "generated_files": generated_files,
            "failed_files": failed_files,
            "sub_questions": sub_questions
        }) + "\n"
        
    except Exception as e:
        yield f"Error: {str(e)}\n"


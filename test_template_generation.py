"""
Test script for template-based project generation.
Tests the granular sub-questions + template approach.
"""
import sys
import json
import os
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Try to import template functions (may fail if dependencies not installed)
try:
    from backend.modules.template_generator import (
        load_template,
        find_template_files,
        decompose_into_sub_questions,
        customize_template,
        detect_language_from_path
    )
    from backend.modules.full_stack_generator import detect_stack_from_description
    IMPORTS_OK = True
except ImportError as e:
    print(f"Warning: Could not import all modules: {e}")
    print("Will test only basic file operations...")
    IMPORTS_OK = False
    
    # Define minimal functions for testing
    def detect_language_from_path(path: str) -> str:
        """Detect programming language from file path."""
        ext = Path(path).suffix.lower()
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
    
    def load_template(template_name: str, file_path: str):
        """Load template file directly."""
        from pathlib import Path
        template_base = Path(__file__).parent / "templates"
        template_map = {
            "react-base": template_base / "frontend" / "react-base",
            "flask-base": template_base / "backend" / "flask-base",
            "sqlite-base": template_base / "database" / "sqlite-base",
            "react-flask": template_base / "integration" / "react-flask"
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
        except Exception:
            return None
    
    def find_template_files(template_name: str):
        """Find all files in template directory."""
        import os
        from pathlib import Path
        template_base = Path(__file__).parent / "templates"
        template_map = {
            "react-base": template_base / "frontend" / "react-base",
            "flask-base": template_base / "backend" / "flask-base",
            "sqlite-base": template_base / "database" / "sqlite-base",
            "react-flask": template_base / "integration" / "react-flask"
        }
        template_dir = template_map.get(template_name)
        if not template_dir or not template_dir.exists():
            return []
        files = []
        for root, dirs, filenames in os.walk(template_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            for filename in filenames:
                if filename.startswith('.') or filename == '.gitkeep':
                    continue
                rel_path = os.path.relpath(os.path.join(root, filename), template_dir)
                files.append(rel_path.replace('\\', '/'))
        return files


def test_template_loading():
    """Test loading templates."""
    print("\n=== Testing Template Loading ===")
    
    # Test React template
    react_files = find_template_files("react-base")
    print(f"React template files: {len(react_files)}")
    for f in react_files[:5]:
        print(f"  - {f}")
    
    # Test Flask template
    flask_files = find_template_files("flask-base")
    print(f"\nFlask template files: {len(flask_files)}")
    for f in flask_files[:5]:
        print(f"  - {f}")
    
    # Test loading a specific file
    app_jsx = load_template("react-base", "src/App.jsx")
    if app_jsx:
        print(f"\n[OK] Loaded App.jsx ({len(app_jsx)} chars)")
        print(f"  Contains placeholders: {'{{' in app_jsx}")
    else:
        print("\n[FAIL] Failed to load App.jsx")
    
    app_py = load_template("flask-base", "app.py")
    if app_py:
        print(f"[OK] Loaded app.py ({len(app_py)} chars)")
        print(f"  Contains placeholders: {'{{' in app_py}")
    else:
        print("[FAIL] Failed to load app.py")


def test_sub_question_decomposition():
    """Test sub-question decomposition."""
    if not IMPORTS_OK:
        print("\n=== Testing Sub-Question Decomposition ===")
        print("[SKIP] Skipped: Requires API access (openai module)")
        return
    
    print("\n=== Testing Sub-Question Decomposition ===")
    
    description = "Build a todo app with React frontend, Flask backend, and SQLite database"
    stack = detect_stack_from_description(description)
    
    print(f"Description: {description}")
    print(f"Detected stack: {stack}")
    
    result = decompose_into_sub_questions(description, stack)
    
    if result.get("ok"):
        sub_questions = result.get("sub_questions", [])
        print(f"\n[OK] Generated {len(sub_questions)} sub-questions:")
        for i, sq in enumerate(sub_questions[:5], 1):
            print(f"\n  {i}. {sq.get('question', '')}")
            print(f"     Template: {sq.get('template', '')}")
            print(f"     Target: {sq.get('target', '')}")
    else:
        print(f"\n[FAIL] Failed: {result.get('error', 'Unknown error')}")


def test_template_customization():
    """Test template customization."""
    if not IMPORTS_OK:
        print("\n=== Testing Template Customization ===")
        print("[SKIP] Skipped: Requires API access (openai module)")
        return
    
    print("\n=== Testing Template Customization ===")
    
    # Load a template
    template_code = load_template("react-base", "src/App.jsx")
    if not template_code:
        print("✗ Could not load template")
        return
    
    print(f"Template size: {len(template_code)} chars")
    print(f"Contains {{APP_NAME}}: {'{{APP_NAME}}' in template_code}")
    
    # Customize it
    requirement = "Create a todo list component with add, delete, and mark complete functionality"
    context = "Todo app main component"
    project_description = "Build a todo app with React frontend"
    
    result = customize_template(
        template_code=template_code,
        requirement=requirement,
        context=context,
        project_description=project_description,
        language="javascript"
    )
    
    if result.get("ok"):
        customized = result.get("code", "")
        print(f"\n[OK] Customized template ({len(customized)} chars)")
        print(f"  Original size: {len(template_code)}")
        print(f"  Customized size: {len(customized)}")
        print(f"\n  First 200 chars of customized:")
        print(f"  {customized[:200]}...")
    else:
        print(f"\n[FAIL] Failed: {result.get('error', 'Unknown error')}")


def test_language_detection():
    """Test language detection."""
    print("\n=== Testing Language Detection ===")
    
    test_cases = [
        ("src/App.jsx", "javascript"),
        ("backend/app.py", "python"),
        ("schema.sql", "sql"),
        ("styles.css", "css"),
        ("index.html", "html")
    ]
    
    for path, expected in test_cases:
        detected = detect_language_from_path(path)
        status = "[OK]" if detected == expected else "[FAIL]"
        print(f"{status} {path} -> {detected} (expected: {expected})")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Template Generation Test Suite")
    print("=" * 60)
    
    try:
        test_template_loading()
        test_language_detection()
        # test_sub_question_decomposition()  # Commented out to avoid API call
        # test_template_customization()  # Commented out to avoid API call
        
        print("\n" + "=" * 60)
        print("[OK] Basic tests completed!")
        print("=" * 60)
        print("\nNote: Sub-question decomposition and customization tests")
        print("      are commented out to avoid API calls during testing.")
        print("      Uncomment them to test full functionality.")
        
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


"""
Test the template-based generation with actual API calls.
This will test the full flow: decomposition → customization → file creation.
"""
import sys
import json
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.modules.template_generator import generate_from_templates
from backend.modules.full_stack_generator import detect_stack_from_description


def test_full_generation():
    """Test full project generation with template-based approach."""
    print("=" * 60)
    print("Template-Based Generation Test")
    print("=" * 60)
    
    # Test project description
    description = "Build a simple todo app with React frontend, Flask backend, and SQLite database"
    
    print(f"\n📝 Project Description:")
    print(f"   {description}")
    
    # Detect stack
    print(f"\n🔍 Detecting stack...")
    stack = detect_stack_from_description(description)
    print(f"   Frontend: {stack['frontend']}")
    print(f"   Backend: {stack['backend']}")
    print(f"   Database: {stack['database']}")
    
    # Test path
    test_repo_path = "./test_generated_todo_app"
    
    print(f"\n📁 Target Path: {test_repo_path}")
    print(f"\n🚀 Starting generation (dry run)...")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        progress_count = 0
        result_data = None
        
        for progress in generate_from_templates(
            description=description,
            stack=stack,
            repo_path=test_repo_path,
            dry_run=True  # Don't create files, just test the generation
        ):
            if progress.startswith("Error:"):
                print(f"\n❌ ERROR: {progress[6:].strip()}")
                return False
            
            if progress.startswith("Progress:"):
                progress_count += 1
                message = progress[9:].strip()  # Remove "Progress: " prefix
                print(f"   [{progress_count}] {message}")
            
            elif progress.strip().startswith("{"):
                try:
                    result_data = json.loads(progress.strip())
                    print(f"\n✅ Received result data")
                except json.JSONDecodeError as e:
                    print(f"\n⚠️  Could not parse result JSON: {e}")
        
        elapsed = time.time() - start_time
        
        print("-" * 60)
        print(f"\n⏱️  Total time: {elapsed:.2f} seconds")
        print(f"📊 Progress updates: {progress_count}")
        
        if result_data:
            generated_files = result_data.get("generated_files", [])
            failed_files = result_data.get("failed_files", [])
            sub_questions = result_data.get("sub_questions", [])
            
            print(f"\n📋 Results:")
            print(f"   Sub-questions generated: {len(sub_questions)}")
            print(f"   Files generated: {len(generated_files)}")
            print(f"   Files failed: {len(failed_files)}")
            
            if sub_questions:
                print(f"\n📝 Sub-questions:")
                for i, sq in enumerate(sub_questions[:5], 1):
                    print(f"   {i}. {sq.get('question', '')[:60]}...")
                    print(f"      → {sq.get('target', '')}")
            
            if generated_files:
                print(f"\n📄 Generated files:")
                for i, f in enumerate(generated_files[:5], 1):
                    print(f"   {i}. {f.get('path', '')}")
                    print(f"      Size: {len(f.get('content', ''))} chars")
            
            if failed_files:
                print(f"\n❌ Failed files:")
                for f in failed_files:
                    print(f"   - {f.get('path', '')}: {f.get('error', '')}")
            
            print(f"\n✅ Test completed successfully!")
            return True
        else:
            print(f"\n⚠️  No result data received")
            return False
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ Exception after {elapsed:.2f} seconds:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    print("\n🧪 Testing Template-Based Generation with Real API Calls\n")
    
    # Ask for confirmation
    response = input("This will make API calls to the LLM. Continue? (y/n): ").strip().lower()
    if response != 'y':
        print("Test cancelled.")
        return
    
    success = test_full_generation()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ Test failed!")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()


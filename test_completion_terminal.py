"""
Simple terminal test for completion endpoint.
Easy to run from command line.
"""
import requests
import json
import sys

SERVER_URL = "http://127.0.0.1:5050"

def test_completion_simple():
    """Simple test you can run from terminal."""
    print("=" * 60)
    print("COMPLETION ENDPOINT TEST (Terminal)")
    print("=" * 60)
    print()
    
    # Test with your actual page.tsx content
    file_content = """// app/experience/page.tsx
import Section from "@/components/Section";
import ExperienceItem from "@/components/ExperienceItem";
import { experience } from "@/data/experience";

export const metadata = {
  title: "Experience - 宝贝的个人网站",
  description: "Internships and work experience",
};

export default function ExperiencePage() {
  return (
    <Section title="Experience">
      <div className="space-y-6">
        {experience.map((e) => (
          <ExperienceItem key={`${e.company}-${e.time}`} item={e} />
        ))}
      </div>
    </Section>
  );
}

//have to do a test code
if
"""
    
    # Count actual lines
    lines = file_content.splitlines()
    actual_lines = len(lines)
    
    print("Testing completion for page.tsx...")
    print(f"File content: {len(file_content)} characters")
    print(f"Total lines: {actual_lines}")
    print("Cursor position: After 'if' keyword (last line)")
    print()
    print("Sending request to backend...")
    print()
    
    try:
        response = requests.post(
            f"{SERVER_URL}/completion",
            json={
                "file_path": "app/experience/page.tsx",
                "file_content": file_content,
                "cursor_line": actual_lines,  # Last line (after "if")
                "cursor_column": 3,  # After "if"
                "repo_dir": None,  # Optional
                "num_completions": 1,
                "max_tokens": 200
            },
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            print("Response Data:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print()
            
            if data.get("ok") and data.get("primary_completion"):
                completion = data["primary_completion"]
                print("=" * 60)
                print("COMPLETION GENERATED:")
                print("=" * 60)
                print(completion)
                print("=" * 60)
                print()
                print(f"Length: {len(completion)} characters")
                print()
                print("SUCCESS: Backend is generating completions!")
                return True
            else:
                print("ERROR: No completion generated")
                print(f"Error: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server!")
        print(f"Make sure server is running: http://{SERVER_URL}/health")
        print()
        print("Start server with:")
        print("  python -m backend.app")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    success = test_completion_simple()
    print()
    if success:
        print("=" * 60)
        print("Backend is working! If ghost text doesn't appear in VS Code,")
        print("the issue is with the extension, not the backend.")
        print("=" * 60)
    else:
        print("=" * 60)
        print("Backend test failed. Check the errors above.")
        print("=" * 60)
    print()


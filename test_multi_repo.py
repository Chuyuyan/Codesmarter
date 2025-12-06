"""
Test script for multi-repo support.
Tests indexing and querying multiple repositories.
"""
import sys
import time
import json
import requests
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SERVER_URL = "http://127.0.0.1:5050"

# Example repositories (adjust paths as needed)
TEST_REPOS = [
    r"C:\Users\57811\my-portfolio",
    # Add more repo paths here for testing
    # r"C:\Users\57811\another-repo",
]

def check_server():
    """Check if server is running."""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def list_repos():
    """List all indexed repositories."""
    print("\n📋 Listing indexed repositories...")
    try:
        response = requests.get(f"{SERVER_URL}/repos", timeout=10)
        data = response.json()
        
        if data.get("ok"):
            repos = data.get("repos", [])
            print(f"✅ Found {len(repos)} indexed repository(ies):")
            for repo in repos:
                print(f"   - {repo.get('repo_id')}: {repo.get('chunks', 0)} chunks")
            return True
        else:
            print(f"❌ Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def index_multiple_repos(repo_dirs):
    """Index multiple repositories."""
    print("\n" + "=" * 60)
    print("🧪 Test 1: Index Multiple Repositories")
    print("=" * 60)
    
    body = {
        "repo_dirs": repo_dirs
    }
    
    print(f"\n📋 Indexing {len(repo_dirs)} repositories...")
    for repo_dir in repo_dirs:
        print(f"   - {repo_dir}")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/index_repo",
            json=body,
            timeout=300  # 5 minutes for indexing
        )
        data = response.json()
        
        if data.get("ok"):
            repos = data.get("repos", [])
            print(f"\n✅ Indexing completed!")
            success_count = 0
            for repo_info in repos:
                if repo_info.get("ok"):
                    success_count += 1
                    print(f"   ✅ {repo_info.get('repo_id')}: {repo_info.get('chunks', 0)} chunks")
                else:
                    print(f"   ❌ {repo_info.get('repo_id') or repo_info.get('repo_dir')}: {repo_info.get('error')}")
            
            print(f"\n📊 Summary: {success_count}/{len(repos)} repositories indexed successfully")
            return success_count > 0
        else:
            print(f"\n❌ Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False

def search_multiple_repos(repo_dirs, query):
    """Search across multiple repositories."""
    print("\n" + "=" * 60)
    print("🧪 Test 2: Search Across Multiple Repositories")
    print("=" * 60)
    
    body = {
        "repo_dirs": repo_dirs,
        "query": query,
        "k": 10
    }
    
    print(f"\n📋 Request:")
    print(f"   Query: '{query}'")
    print(f"   Repositories: {len(repo_dirs)}")
    for repo_dir in repo_dirs:
        print(f"     - {Path(repo_dir).name}")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/search",
            json=body,
            timeout=60
        )
        data = response.json()
        
        if data.get("ok"):
            results = data.get("results", [])
            print(f"\n✅ Search completed!")
            print(f"   Found {len(results)} results across repositories")
            print(f"   Mode: {data.get('mode')}")
            print(f"   Repos searched: {data.get('repos_searched')}")
            
            # Group results by repo
            by_repo = {}
            for result in results:
                repo_id = result.get("repo_id", "unknown")
                if repo_id not in by_repo:
                    by_repo[repo_id] = []
                by_repo[repo_id].append(result)
            
            print(f"\n📊 Results by repository:")
            for repo_id, repo_results in by_repo.items():
                print(f"   - {repo_id}: {len(repo_results)} results")
                # Show first result from each repo
                if repo_results:
                    first = repo_results[0]
                    file_name = Path(first.get("file", "")).name
                    print(f"     Example: {file_name} (score: {first.get('score_vec', 0):.4f})")
            
            return True
        else:
            print(f"\n❌ Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False

def chat_multiple_repos(repo_dirs, question):
    """Chat across multiple repositories."""
    print("\n" + "=" * 60)
    print("🧪 Test 3: Chat Across Multiple Repositories")
    print("=" * 60)
    
    body = {
        "repo_dirs": repo_dirs,
        "question": question,
        "analysis_type": "explain",
        "top_k": 10
    }
    
    print(f"\n📋 Request:")
    print(f"   Question: '{question}'")
    print(f"   Repositories: {len(repo_dirs)}")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/chat",
            json=body,
            timeout=120
        )
        data = response.json()
        
        if data.get("ok"):
            print(f"\n✅ Chat completed!")
            print(f"   Mode: {data.get('mode')}")
            print(f"   Repos: {data.get('repo_ids', [])}")
            print(f"   Evidences: {len(data.get('evidences', []))}")
            
            answer = data.get("answer", "")
            print(f"\n📝 Answer (first 300 chars):")
            print("-" * 60)
            print(answer[:300] + ("..." if len(answer) > 300 else ""))
            print("-" * 60)
            
            # Show which repos contributed
            evidences = data.get("evidences", [])
            repo_contributions = {}
            for ev in evidences:
                repo_id = ev.get("repo_id", "unknown")
                repo_contributions[repo_id] = repo_contributions.get(repo_id, 0) + 1
            
            if repo_contributions:
                print(f"\n📊 Code snippets by repository:")
                for repo_id, count in repo_contributions.items():
                    print(f"   - {repo_id}: {count} snippet(s)")
            
            return True
        else:
            print(f"\n❌ Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False

def main():
    """Run all multi-repo tests."""
    print("=" * 60)
    print("🔧 Testing Multi-Repo Support")
    print("=" * 60)
    
    # Check server
    print("\n🔌 Checking server...")
    if not check_server():
        print(f"❌ Server not running at {SERVER_URL}")
        print("   Please start the server: python -m backend.app")
        return False
    print("✅ Server is running")
    
    # Filter test repos to only those that exist
    existing_repos = [r for r in TEST_REPOS if Path(r).exists()]
    
    if not existing_repos:
        print("\n⚠️  No test repositories found!")
        print("   Please update TEST_REPOS list in test_multi_repo.py")
        print("   with paths to repositories you want to test.")
        return False
    
    print(f"\n📁 Found {len(existing_repos)} test repository(ies)")
    
    # Run tests
    results = []
    
    # Test 0: List repos
    results.append(("List repos", list_repos()))
    
    # Test 1: Index multiple repos
    if len(existing_repos) >= 1:
        results.append(("Index multiple repos", index_multiple_repos(existing_repos[:2])))  # Test with up to 2 repos
    
    # Test 2: Search across repos
    if len(existing_repos) >= 1:
        test_repos = existing_repos[:2] if len(existing_repos) >= 2 else existing_repos
        results.append(("Search multiple repos", search_multiple_repos(test_repos, "function component")))
    
    # Test 3: Chat across repos
    if len(existing_repos) >= 1:
        test_repos = existing_repos[:2] if len(existing_repos) >= 2 else existing_repos
        results.append(("Chat multiple repos", chat_multiple_repos(test_repos, "What is the main structure of these projects?")))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {name}: {status}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Multi-repo support is working.")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
    
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)


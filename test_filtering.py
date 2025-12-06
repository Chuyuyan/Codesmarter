"""Test file filtering functionality"""
from pathlib import Path
from backend.modules.parser import iter_text_files, load_gitignore

root = Path(r"C:\Users\57811\my-portfolio")

print("=" * 60)
print("TESTING FILE FILTERING")
print("=" * 60)

# Load ignore patterns
patterns = load_gitignore(root)
print(f"\nLoaded {len(patterns)} ignore patterns")
print("\nSample patterns:")
for p in list(patterns)[:10]:
    print(f"  - {p}")

# Test file iteration
print("\n" + "=" * 60)
print("Iterating files with filtering...")
print("=" * 60)

files = list(iter_text_files(root))
print(f"\nTotal files found: {len(files)}")

# Check if node_modules is excluded
node_modules_files = [f for f in files if 'node_modules' in str(f)]
print(f"Files in node_modules: {len(node_modules_files)}")

# Check if .git is excluded
git_files = [f for f in files if '.git' in str(f)]
print(f"Files in .git: {len(git_files)}")

# Check if .next is excluded
next_files = [f for f in files if '.next' in str(f)]
print(f"Files in .next: {len(next_files)}")

# Show some actual files
print("\nFirst 10 files found:")
for f in files[:10]:
    print(f"  {f}")

print("\n" + "=" * 60)
if len(node_modules_files) == 0 and len(git_files) == 0 and len(next_files) == 0:
    print("SUCCESS! Filtering is working correctly!")
else:
    print("WARNING: Some files that should be filtered are still present")
print("=" * 60)


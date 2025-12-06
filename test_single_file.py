"""Test semantic chunking on a single file"""
from pathlib import Path
from backend.modules.parser import semantic_chunks
import re

test_file = Path(r"C:\Users\57811\my-portfolio\app\page.tsx")

print("=" * 60)
print(f"Testing semantic chunking on: {test_file.name}")
print("=" * 60)

# Read first few lines
with open(test_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()[:5]
    print("\nFirst 5 lines:")
    for i, line in enumerate(lines, 1):
        print(f"{i}: {line.rstrip()}")

# Test pattern matching
print("\n" + "=" * 60)
print("Testing pattern matching:")
print("=" * 60)

first_line = lines[0].rstrip()
print(f"First line: {first_line}")

patterns = [
    r'export\s+default\s+function\s+\w+\s*\([^)]*\)\s*\{',
    r'export\s+function\s+\w+\s*\([^)]*\)\s*\{',
    r'(export\s+)?(async\s+)?function\s+\w+\s*\([^)]*\)\s*\{',
]

for i, pattern in enumerate(patterns, 1):
    match = re.search(pattern, first_line)
    print(f"Pattern {i}: {bool(match)} - {pattern[:50]}...")

# Test semantic chunking
print("\n" + "=" * 60)
print("Testing semantic_chunks function:")
print("=" * 60)

chunks = semantic_chunks(test_file)
print(f"Chunks returned: {len(chunks)}")
if chunks:
    print(f"First chunk type: {chunks[0].get('type')}")
    print(f"First chunk preview: {chunks[0]['snippet'][:100]}...")
else:
    print("No chunks returned - will use fallback")


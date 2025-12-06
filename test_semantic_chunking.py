"""Test semantic chunking functionality"""
from pathlib import Path
from backend.modules.parser import semantic_chunks, fallback_line_chunks, slice_repo

print("=" * 60)
print("TESTING SEMANTIC CHUNKING")
print("=" * 60)

# Test with a Python file if available
test_repo = Path(r"C:\Users\57811\my-portfolio")

print("\n1. Testing semantic chunking on repository...")
chunks = slice_repo(str(test_repo), use_semantic=True)

print(f"\nTotal chunks: {len(chunks)}")

# Analyze chunk types
chunk_types = {}
for chunk in chunks:
    chunk_type = chunk.get("type", "unknown")
    chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

print("\nChunk types breakdown:")
for chunk_type, count in chunk_types.items():
    print(f"  {chunk_type}: {count}")

# Show some examples
print("\n" + "=" * 60)
print("Sample semantic chunks:")
print("=" * 60)

semantic_examples = [c for c in chunks if c.get("type") in ["function", "class"]]
for i, chunk in enumerate(semantic_examples[:5], 1):
    print(f"\n{i}. {chunk.get('type', 'unknown').upper()} chunk:")
    print(f"   File: {Path(chunk['file']).name}")
    print(f"   Lines: {chunk['start']}-{chunk['end']}")
    snippet_preview = chunk['snippet'][:150].replace('\n', ' ').encode('ascii', 'ignore').decode('ascii')
    print(f"   Preview: {snippet_preview}...")

print("\n" + "=" * 60)
if semantic_examples:
    print("SUCCESS! Semantic chunking is working!")
    print(f"Found {len(semantic_examples)} semantic units (functions/classes)")
else:
    print("No semantic chunks found - using fallback line-based chunking")
print("=" * 60)


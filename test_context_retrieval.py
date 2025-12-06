"""
Test script for enhanced context retrieval.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from backend.modules.context_retriever import expand_code_context, expand_to_semantic_boundaries, get_imports

# Test with sample evidences
test_evidences = [
    {
        "file": str(Path(__file__).parent / "backend" / "app.py"),
        "start": 160,
        "end": 165,
        "snippet": "rg_results = ripgrep_candidates(question, repo_dir)",
        "score_vec": 0.8
    }
]

print("=== Testing Enhanced Context Retrieval ===\n")

repo_dir = str(Path(__file__).parent)

print(f"Repository: {repo_dir}")
print(f"Test evidences: {len(test_evidences)}")
print(f"Sample evidence: {test_evidences[0]['file']}:{test_evidences[0]['start']}-{test_evidences[0]['end']}")

print("\n--- Expanding context ---")
enhanced = expand_code_context(test_evidences, repo_dir, context_lines=10)

if enhanced:
    print(f"✅ Enhanced {len(enhanced)} evidences")
    for i, ev in enumerate(enhanced):
        print(f"\nEvidence {i+1}:")
        print(f"  File: {Path(ev['file']).name}")
        print(f"  Original: {ev.get('original_start', ev['start'])}-{ev.get('original_end', ev['end'])}")
        print(f"  Expanded: {ev['start']}-{ev['end']}")
        print(f"  Has imports: {ev.get('has_imports', False)}")
        snippet = ev['snippet']
        print(f"  Snippet length: {len(snippet)} chars")
        print(f"  First 100 chars: {snippet[:100]}...")
else:
    print("❌ No enhanced evidences returned")

print("\n✅ Test completed!")


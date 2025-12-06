"""
Simple test for 'generate' analysis type detection.
Doesn't require server to be running.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.modules.analysis_detector import detect_analysis_type, detect_analysis_type_keywords


def test_generate_detection():
    """Test that 'generate' is detected correctly."""
    print("\n" + "="*60)
    print("Testing 'Generate' Analysis Type Detection")
    print("="*60)
    
    test_cases = [
        ("Build me a todo app with React and Flask", "generate"),
        ("Create a blog with authentication", "generate"),
        ("I want to build a full-stack e-commerce site", "generate"),
        ("Generate a project with frontend and backend", "generate"),
        ("Make me a todo app", "generate"),
        ("I want to create a web application", "generate"),
        ("Build a full stack application", "generate"),
        ("How does authentication work?", "explain"),  # Should NOT be generate
        ("Why is this function slow?", "optimize"),  # Should NOT be generate
    ]
    
    print("\nTest Cases:")
    print("-" * 60)
    
    passed = 0
    total = len(test_cases)
    
    for question, expected in test_cases:
        # Get keyword scores
        scores = detect_analysis_type_keywords(question)
        max_score = max(scores.values())
        detected = detect_analysis_type(question, use_llm=False)
        
        status = "[PASS]" if detected == expected else "[FAIL]"
        if detected == expected:
            passed += 1
        
        print(f"{status} '{question[:55]}...'")
        print(f"      Expected: {expected:10} | Got: {detected:10} | Score: {max_score}")
        if detected != expected:
            print(f"      Scores: {scores}")
        print()
    
    print("="*60)
    print(f"Results: {passed}/{total} passed ({passed*100//total}%)")
    print("="*60)
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
    else:
        print(f"\n[PARTIAL] {total - passed} test(s) failed")
        print("Note: Some may need LLM detection for better accuracy")
    
    return passed == total


if __name__ == "__main__":
    test_generate_detection()


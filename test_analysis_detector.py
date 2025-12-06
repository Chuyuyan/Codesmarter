"""
Test script for analysis type detection.
Shows how keyword-based and LLM-based detection work.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.modules.analysis_detector import (
    detect_analysis_type,
    detect_analysis_type_keywords,
    get_analysis_type_with_confidence
)


def test_detection(question: str, expected: str, use_llm: bool = False):
    """Test detection and show results."""
    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"Expected: {expected}")
    print(f"{'='*60}")
    
    # Get keyword scores
    scores = detect_analysis_type_keywords(question)
    max_score = max(scores.values())
    
    print(f"\nKeyword Scores:")
    for analysis_type, score in scores.items():
        marker = " ←" if score == max_score else ""
        print(f"  {analysis_type:10} : {score:2} {marker}")
    
    # Get confidence info (with use_llm parameter)
    confidence_info = get_analysis_type_with_confidence(question, use_llm=use_llm)
    print(f"\nConfidence: {confidence_info['confidence']:.2%}")
    print(f"Method: {confidence_info['method']}")
    
    # Detect type
    detected = detect_analysis_type(question, use_llm=use_llm)
    
    # Check result
    status = "[PASS] CORRECT" if detected == expected else "[FAIL] WRONG"
    print(f"\nDetected: {detected}")
    print(f"Result: {status}")
    
    if detected != expected:
        print(f"[WARN] Expected '{expected}' but got '{detected}'")
    
    return detected == expected


def main():
    """Run test cases."""
    print("\n" + "="*60)
    print("Analysis Type Detection Test Suite")
    print("="*60)
    
    # Test cases: (question, expected_type, use_llm)
    test_cases = [
        # High confidence (score >= 2) - keyword should work
        ("How does authentication work in this codebase?", "explain", False),
        ("Why is this function so slow and has performance issues?", "optimize", False),
        ("There's a bug and an error in this code", "debug", False),
        ("How can I improve and refactor this code?", "refactor", False),
        
        # Medium confidence (score = 1) - keyword might work
        ("Why is this function slow?", "optimize", False),
        ("There's a bug here", "debug", False),
        ("Explain this code", "explain", False),
        ("Refactor this function", "refactor", False),
        
        # Low confidence (score = 0 or ambiguous) - might need LLM
        ("This code seems inefficient", "optimize", False),  # Now has "inefficient" keyword
        ("Something's not right", "debug", False),  # Now has "not right" pattern
        ("Can you help with this?", "explain", False),  # Default
        ("This needs work", "refactor", False),  # Might need LLM
        
        # Edge cases
        ("", "explain", False),  # Empty
        ("What?", "explain", False),  # Too short
    ]
    
    results = []
    for question, expected, use_llm in test_cases:
        correct = test_detection(question, expected, use_llm)
        results.append((question, expected, correct))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    correct_count = sum(1 for _, _, correct in results if correct)
    total_count = len(results)
    accuracy = (correct_count / total_count) * 100
    
    print(f"\nTotal Tests: {total_count}")
    print(f"Correct: {correct_count}")
    print(f"Wrong: {total_count - correct_count}")
    print(f"Accuracy: {accuracy:.1f}%")
    
    print("\nFailed Tests:")
    for question, expected, correct in results:
        if not correct:
            detected = detect_analysis_type(question, use_llm=False)
            print(f"  [FAIL] '{question[:50]}...'")
            print(f"     Expected: {expected}, Got: {detected}")
    
    print("\n" + "="*60)
    print("Note: Some tests may fail with keyword-only detection.")
    print("Enable LLM (use_llm=True) for better accuracy on ambiguous questions.")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()


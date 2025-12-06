# Auto Analysis Type Detection: Implementation Plan

## 🎯 Goal

Automatically detect the best analysis type (`explain`, `refactor`, `debug`, `optimize`) from the user's question, so users don't have to manually choose.

## 💡 Current Problem

**Before:**
```python
POST /chat {
  "question": "Why is this function slow?",
  "analysis_type": "optimize"  # User must manually specify
}
```

**Problem:**
- ❌ User has to know which type to choose
- ❌ Extra step in the workflow
- ❌ Can choose wrong type
- ❌ Less user-friendly

## ✅ Proposed Solution

**After:**
```python
POST /chat {
  "question": "Why is this function slow?"
  # No analysis_type needed - auto-detected!
}
```

**Benefits:**
- ✅ Automatic detection from question
- ✅ User-friendly (no manual choice)
- ✅ Can still override if needed
- ✅ Smart defaults

## 🔍 Detection Strategy

### **Method 1: Keyword-Based Detection** (Fast, Simple)

**How it works:**
- Analyze question for keywords
- Match keywords to analysis types
- Choose type with most matches

**Keywords:**
```python
ANALYSIS_KEYWORDS = {
    "explain": [
        "how does", "what does", "explain", "understand", 
        "how it works", "what is", "tell me about",
        "describe", "walk me through", "help me understand"
    ],
    "refactor": [
        "refactor", "improve", "clean up", "make it better",
        "code quality", "maintainability", "readability",
        "restructure", "reorganize", "better code"
    ],
    "debug": [
        "bug", "error", "issue", "problem", "not working",
        "broken", "fix", "wrong", "fails", "crash",
        "exception", "debug", "what's wrong", "why doesn't"
    ],
    "optimize": [
        "slow", "performance", "optimize", "faster",
        "speed", "bottleneck", "efficient", "optimization",
        "make it faster", "why is it slow", "improve speed"
    ]
}
```

**Example:**
```python
question = "Why is this function slow?"
# Matches: "slow" → optimize
# Result: analysis_type = "optimize"
```

**Pros:**
- ✅ Fast (no LLM call)
- ✅ Simple to implement
- ✅ Works for most cases

**Cons:**
- ⚠️ May miss nuanced questions
- ⚠️ False positives possible

---

### **Method 2: LLM-Based Detection** (Smart, Accurate)

**How it works:**
- Use LLM to analyze question intent
- LLM determines best analysis type
- More accurate than keywords

**Prompt:**
```python
DETECTION_PROMPT = """
Analyze this question and determine the best analysis type:
- "explain": User wants to understand how code works
- "refactor": User wants to improve code quality/maintainability
- "debug": User wants to find bugs or fix issues
- "optimize": User wants to improve performance/speed

Question: {question}

Respond with ONLY one word: explain, refactor, debug, or optimize
"""
```

**Example:**
```python
question = "This code seems inefficient, how can I make it better?"
# LLM analyzes: "inefficient" + "make it better" → optimize
# Result: analysis_type = "optimize"
```

**Pros:**
- ✅ Very accurate
- ✅ Handles nuanced questions
- ✅ Understands context

**Cons:**
- ⚠️ Slower (requires LLM call)
- ⚠️ Costs API tokens
- ⚠️ More complex

---

### **Method 3: Hybrid Approach** ⭐ (RECOMMENDED)

**How it works:**
1. First try keyword-based (fast, free)
2. If confidence is low, use LLM (accurate)
3. Fallback to "explain" if uncertain

**Algorithm:**
```python
def detect_analysis_type(question: str) -> str:
    # Step 1: Keyword detection
    scores = count_keyword_matches(question)
    max_score = max(scores.values())
    
    # Step 2: Check confidence
    if max_score >= 2:  # High confidence
        return max(scores, key=scores.get)
    
    # Step 3: Use LLM for ambiguous cases
    if max_score == 1:  # Low confidence
        return llm_detect_analysis_type(question)
    
    # Step 4: Default fallback
    return "explain"
```

**Benefits:**
- ✅ Fast for clear questions (keyword-based)
- ✅ Accurate for ambiguous questions (LLM-based)
- ✅ Cost-effective (LLM only when needed)
- ✅ Best of both worlds

---

## 🚀 Implementation Plan

### **Step 1: Create Detection Module**

Create `backend/modules/analysis_detector.py`:

```python
"""
Automatic analysis type detection from user questions.
"""
import re
from typing import Dict, Optional

# Keyword patterns for each analysis type
ANALYSIS_KEYWORDS = {
    "explain": [
        r"how\s+does", r"what\s+does", r"explain", r"understand",
        r"how\s+it\s+works", r"what\s+is", r"tell\s+me\s+about",
        r"describe", r"walk\s+me\s+through", r"help\s+me\s+understand",
        r"can\s+you\s+explain", r"what's\s+this", r"how\s+this\s+works"
    ],
    "refactor": [
        r"refactor", r"improve", r"clean\s+up", r"make\s+it\s+better",
        r"code\s+quality", r"maintainability", r"readability",
        r"restructure", r"reorganize", r"better\s+code",
        r"how\s+can\s+I\s+improve", r"make\s+this\s+cleaner"
    ],
    "debug": [
        r"bug", r"error", r"issue", r"problem", r"not\s+working",
        r"broken", r"fix", r"wrong", r"fails", r"crash",
        r"exception", r"debug", r"what's\s+wrong", r"why\s+doesn't",
        r"why\s+isn't", r"doesn't\s+work", r"not\s+functioning"
    ],
    "optimize": [
        r"slow", r"performance", r"optimize", r"faster",
        r"speed", r"bottleneck", r"efficient", r"optimization",
        r"make\s+it\s+faster", r"why\s+is\s+it\s+slow", r"improve\s+speed",
        r"performance\s+issue", r"too\s+slow", r"optimization"
    ]
}

def detect_analysis_type_keywords(question: str) -> Dict[str, int]:
    """
    Detect analysis type using keyword matching.
    Returns scores for each type.
    """
    question_lower = question.lower()
    scores = {type_name: 0 for type_name in ANALYSIS_KEYWORDS.keys()}
    
    for analysis_type, patterns in ANALYSIS_KEYWORDS.items():
        for pattern in patterns:
            matches = len(re.findall(pattern, question_lower, re.IGNORECASE))
            scores[analysis_type] += matches
    
    return scores

def detect_analysis_type(question: str, use_llm: bool = False) -> str:
    """
    Automatically detect analysis type from question.
    
    Args:
        question: User's question
        use_llm: If True, use LLM for detection (more accurate but slower)
    
    Returns:
        Analysis type: "explain", "refactor", "debug", or "optimize"
    """
    # Step 1: Keyword-based detection
    scores = detect_analysis_type_keywords(question)
    max_score = max(scores.values())
    best_type = max(scores, key=scores.get)
    
    # Step 2: Check confidence
    if max_score >= 2:
        # High confidence - use keyword result
        return best_type
    
    # Step 3: Use LLM for ambiguous cases (if enabled)
    if use_llm and max_score == 1:
        try:
            from backend.modules.llm_api import get_fresh_client
            client = get_fresh_client()
            
            prompt = f"""Analyze this question and determine the best analysis type:
- "explain": User wants to understand how code works
- "refactor": User wants to improve code quality/maintainability  
- "debug": User wants to find bugs or fix issues
- "optimize": User wants to improve performance/speed

Question: {question}

Respond with ONLY one word: explain, refactor, debug, or optimize"""
            
            response = client.chat.completions.create(
                model="deepseek-chat",  # Use fast model for detection
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            detected = response.choices[0].message.content.strip().lower()
            if detected in ["explain", "refactor", "debug", "optimize"]:
                return detected
        except Exception as e:
            print(f"[analysis_detector] LLM detection failed: {e}")
    
    # Step 4: Default fallback
    if max_score == 0:
        return "explain"  # Default for unclear questions
    
    return best_type  # Use keyword result even if low confidence
```

### **Step 2: Update Chat Endpoint**

Modify `/chat` endpoint in `backend/app.py`:

```python
@app.post("/chat")
def answer():
    # ... existing code ...
    
    question = data.get("question") or data.get("query")
    analysis_type = data.get("analysis_type")  # Optional - can be None
    
    # Auto-detect if not provided
    if not analysis_type:
        from backend.modules.analysis_detector import detect_analysis_type
        analysis_type = detect_analysis_type(question, use_llm=False)
        print(f"[chat] Auto-detected analysis type: {analysis_type}")
    
    # ... rest of code uses analysis_type ...
```

### **Step 3: Update Other Endpoints**

Apply same logic to:
- `/agent` endpoint
- `/refactor` endpoint (can auto-detect if not specified)
- Any other endpoints using `analysis_type`

---

## 📊 Examples

### **Example 1: Clear Question**
```python
question = "Why is this function so slow?"
detect_analysis_type(question)
# Result: "optimize" (keyword: "slow")
```

### **Example 2: Ambiguous Question**
```python
question = "Can you help me with this code?"
detect_analysis_type(question)
# Result: "explain" (default fallback)
```

### **Example 3: Multiple Keywords**
```python
question = "This code has a bug and it's also very slow"
detect_analysis_type(question)
# Result: "debug" (more "bug" matches than "slow")
```

### **Example 4: With LLM**
```python
question = "This implementation seems suboptimal"
detect_analysis_type(question, use_llm=True)
# Keywords: No clear match
# LLM: Analyzes "suboptimal" → "optimize"
# Result: "optimize"
```

---

## 🎯 Benefits

1. **User-Friendly**
   - No manual type selection
   - Just ask naturally
   - System figures it out

2. **Smart Defaults**
   - Works for 90% of questions
   - Keyword-based (fast, free)
   - LLM fallback for edge cases

3. **Flexible**
   - User can still override
   - `analysis_type` parameter still works
   - Backward compatible

4. **Better UX**
   - Less friction
   - More natural interaction
   - Like talking to a colleague

---

## 🔧 Configuration

### **Enable/Disable Auto-Detection**

```python
# In config.py
AUTO_DETECT_ANALYSIS_TYPE = os.getenv("AUTO_DETECT_ANALYSIS_TYPE", "true").lower() in ("true", "1")

# In app.py
if AUTO_DETECT_ANALYSIS_TYPE and not analysis_type:
    analysis_type = detect_analysis_type(question)
```

### **Use LLM for Detection**

```python
# Use LLM for ambiguous cases
analysis_type = detect_analysis_type(question, use_llm=True)
```

---

## 📈 Testing

### **Test Cases:**

```python
test_cases = [
    ("How does authentication work?", "explain"),
    ("This function is too slow", "optimize"),
    ("There's a bug in this code", "debug"),
    ("How can I improve this code?", "refactor"),
    ("What does this do?", "explain"),
    ("Fix this broken function", "debug"),
    ("Make this code faster", "optimize"),
    ("Clean up this messy code", "refactor"),
]
```

---

## ✅ Summary

**Current:** User must specify `analysis_type` manually
**Proposed:** System auto-detects from question
**Method:** Keyword-based (fast) + LLM fallback (accurate)
**Result:** Better UX, more natural interaction

**Implementation:**
1. Create `analysis_detector.py` module
2. Update `/chat` endpoint to auto-detect
3. Keep `analysis_type` parameter (for override)
4. Test with various question types

This makes the system much more user-friendly! 🎉


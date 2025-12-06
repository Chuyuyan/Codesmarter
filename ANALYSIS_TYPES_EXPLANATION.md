# Analysis Types Explained

## 🎯 Why We Have Different Analysis Types

The system supports **4 different analysis types** because **each serves a different purpose**. Think of them as different "modes" or "lenses" to analyze your code.

---

## 📊 The 4 Analysis Types

### 1. **"explain"** 📖 - Understanding Code

**Purpose:** Understand what code does and how it works

**When to Use:**
- You're new to a codebase
- Code is complex and you need clarification
- You want to understand the logic flow
- Onboarding or code review preparation

**What It Does:**
- Explains the purpose of code
- Describes how it works
- Explains the logic flow
- Identifies key concepts

**Example Question:**
```
"How does authentication work in this codebase?"
```

**Example Response:**
```
"The authentication system uses JWT tokens. When a user logs in, 
the server validates credentials and issues a JWT token. This token 
is then sent with each request in the Authorization header..."

[Code citations showing relevant files]
```

**Use Case:** Understanding existing code

---

### 2. **"refactor"** 🔧 - Improving Code Quality

**Purpose:** Suggest improvements to make code cleaner, more maintainable

**When to Use:**
- Code works but could be better
- Code is hard to maintain
- You want to improve code quality
- Before a big refactoring session

**What It Does:**
- Identifies code smells
- Suggests better patterns
- Provides before/after examples
- Focuses on readability and maintainability

**Example Question:**
```
"Refactor this function to be more maintainable"
```

**Example Response:**
```
"Issue: Long function with multiple responsibilities

Before:
[shows original code]

After:
[shows refactored code with extracted functions]

Benefits: Easier to test, clearer intent, better separation of concerns..."
```

**Use Case:** Improving code quality

---

### 3. **"debug"** 🐛 - Finding Bugs & Issues

**Purpose:** Identify bugs, edge cases, and potential problems

**When to Use:**
- Something isn't working
- You suspect there's a bug
- Testing edge cases
- Code review for potential issues

**What It Does:**
- Finds potential bugs
- Identifies edge cases
- Highlights error handling gaps
- Points out logic errors

**Example Question:**
```
"Debug this function - it's not handling errors correctly"
```

**Example Response:**
```
"Potential Issues Found:

1. Null Pointer Exception (Line 15)
   - Variable 'user' might be None
   - Add null check before accessing user.name

2. Missing Error Handling (Line 23)
   - Database call could fail
   - Add try-catch block

3. Edge Case (Line 30)
   - Empty list not handled
   - Add check: if not items: return []..."
```

**Use Case:** Finding and fixing bugs

---

### 4. **"optimize"** ⚡ - Improving Performance

**Purpose:** Make code faster and more efficient

**When to Use:**
- Code is slow
- Performance issues detected
- Before scaling
- Optimization phase

**What It Does:**
- Identifies performance bottlenecks
- Suggests optimizations
- Recommends better algorithms
- Focuses on speed and efficiency

**Example Question:**
```
"Optimize this function - it's too slow"
```

**Example Response:**
```
"Performance Issues:

1. Nested Loop (O(n²) complexity)
   Current: for i in list1: for j in list2: ...
   Optimization: Use dictionary lookup (O(1)) instead

2. Repeated Database Calls
   Current: Queries database inside loop
   Optimization: Batch query all at once

3. Inefficient String Concatenation
   Current: result += str(item)
   Optimization: Use list.join() instead..."
```

**Use Case:** Making code faster

---

## 🔄 How They Work Together

### Different Questions, Different Focus:

**Same Code, Different Analysis:**

```python
def calculate_total(items):
    total = 0
    for item in items:
        total = total + item.price
    return total
```

**"explain":**
> "This function calculates the total price by iterating through items and summing their prices."

**"refactor":**
> "Use `sum()` function: `return sum(item.price for item in items)` - more Pythonic and readable."

**"debug":**
> "Missing null check - what if `items` is None? What if `item.price` is None? Add validation."

**"optimize":**
> "Performance is fine, but if items list is huge, consider using `sum()` with generator expression for memory efficiency."

---

## 💡 Why Separate Types?

### 1. **Different Prompts = Different Focus**

Each type uses a **different prompt** to guide the AI:

```python
prompts = {
    "explain": "Explain what this code does, its purpose, and how it works.",
    "refactor": "Suggest how to refactor this code to make it cleaner...",
    "debug": "Help identify potential bugs, edge cases, or issues...",
    "optimize": "Suggest performance optimizations..."
}
```

**Why?** Because the AI needs different instructions to give you the right type of answer!

---

### 2. **Better User Experience**

**Without Analysis Types:**
- User: "What's wrong with this code?"
- AI: *Gives generic answer mixing explanation, bugs, and refactoring suggestions*
- Result: Confusing, unfocused answer ❌

**With Analysis Types:**
- User: "Debug this code" (analysis_type: "debug")
- AI: *Focuses only on bugs and issues*
- Result: Clear, focused answer ✅

---

### 3. **Context-Aware Responses**

Each type provides **different context** to the AI:

| Type | Focus | Output Style |
|------|-------|--------------|
| **explain** | Understanding | Descriptive, educational |
| **refactor** | Quality | Before/after examples |
| **debug** | Problems | Issue list, fixes |
| **optimize** | Performance | Metrics, optimizations |

---

## 🎯 Real-World Examples

### Scenario 1: New Developer Onboarding

**Task:** Understand authentication system

**Analysis Type:** `"explain"`

**Result:** Clear explanation of how auth works, what files are involved, the flow

---

### Scenario 2: Code Review

**Task:** Review code before merging

**Analysis Type:** `"refactor"` + `"debug"`

**Result:** 
- Refactor suggestions for quality
- Bug identification for safety

---

### Scenario 3: Performance Issues

**Task:** Slow API endpoint

**Analysis Type:** `"optimize"`

**Result:** Specific performance bottlenecks and optimization suggestions

---

### Scenario 4: Bug Fixing

**Task:** Function isn't working correctly

**Analysis Type:** `"debug"`

**Result:** List of potential bugs, edge cases, and fixes

---

## 🔧 How It's Implemented

### In the Code (`backend/modules/llm_api.py`):

```python
def analyze_code(question: str, code_context: List[Dict], analysis_type: str = "explain"):
    """
    Analyze code with different analysis types:
    - explain: Explain what the code does
    - refactor: Suggest refactoring improvements
    - debug: Help debug issues
    - optimize: Suggest performance optimizations
    """
    prompts = {
        "explain": "Explain what this code does, its purpose, and how it works.",
        "refactor": "Suggest how to refactor this code to make it cleaner...",
        "debug": "Help identify potential bugs, edge cases, or issues...",
        "optimize": "Suggest performance optimizations..."
    }
    
    # Prepends the appropriate prompt to your question
    full_question = f"{prompts.get(analysis_type, 'Explain')}\n\nQuestion: {question}"
    return answer_with_citations(full_question, code_context)
```

**How it works:**
1. You choose analysis type
2. System prepends appropriate prompt
3. AI receives focused instruction
4. You get targeted answer

---

## 📊 Comparison Table

| Analysis Type | Focus | Question Style | Output Style |
|--------------|-------|----------------|--------------|
| **explain** | Understanding | "How does X work?" | Descriptive explanation |
| **refactor** | Quality | "How can I improve this?" | Before/after examples |
| **debug** | Problems | "What's wrong here?" | Bug list + fixes |
| **optimize** | Speed | "How can I make this faster?" | Performance suggestions |

---

## 🎯 When to Use Each

### Use **"explain"** when:
- ✅ Learning new code
- ✅ Understanding complex logic
- ✅ Onboarding team members
- ✅ Documentation

### Use **"refactor"** when:
- ✅ Code works but messy
- ✅ Improving maintainability
- ✅ Code review for quality
- ✅ Cleaning up technical debt

### Use **"debug"** when:
- ✅ Something isn't working
- ✅ Finding edge cases
- ✅ Pre-deployment check
- ✅ Bug hunting

### Use **"optimize"** when:
- ✅ Performance issues
- ✅ Slow code
- ✅ Scaling preparation
- ✅ Optimization phase

---

## 💡 Key Insight

**Different analysis types = Different "lenses" to view your code**

- **"explain"** = 🔍 **Microscope** - See details and understand
- **"refactor"** = 🎨 **Designer's Eye** - See how to improve
- **"debug"** = 🐛 **Bug Hunter** - See problems
- **"optimize"** = ⚡ **Performance Engineer** - See bottlenecks

**Same code, different perspectives!**

---

## 🚀 Summary

**Why separate types?**
1. ✅ **Focused answers** - Each type gives targeted responses
2. ✅ **Better prompts** - AI knows what you're looking for
3. ✅ **Better UX** - Users get exactly what they need
4. ✅ **Context-aware** - Different questions need different approaches

**Bottom Line:** It's like asking different experts about the same code - each gives you a different valuable perspective! 🎯


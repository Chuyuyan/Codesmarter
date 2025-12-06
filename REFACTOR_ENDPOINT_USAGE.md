# Refactoring Endpoint Usage Guide

## Overview

The `/refactor` endpoint provides dedicated refactoring suggestions with before/after examples. It supports three ways to provide code for refactoring.

## Endpoint

```
POST /refactor
```

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `repo_dir` | string | Conditional | Repository directory path (required for `query` or `file_path` mode) |
| `query` | string | Conditional | Search query to find code to refactor |
| `file_path` | string | Conditional | Specific file path to refactor (relative to repo_dir) |
| `code_snippets` | array | Conditional | Direct code snippets (list of objects with `file`, `start`, `end`, `snippet`) |
| `focus` | string | Optional | Focus area: "performance", "readability", "maintainability", "design patterns", etc. |
| `top_k` | integer | Optional | Number of code snippets to analyze (default: 5, used with `query`) |

**Note:** You must provide exactly one of: `code_snippets`, `file_path`, or `query`.

## Response Format

```json
{
  "ok": true,
  "refactoring_suggestions": "Markdown-formatted suggestions with before/after examples",
  "code_context": [...],  // Original code snippets analyzed
  "focus": "readability",
  "format": "markdown",
  "count": 3  // Number of code snippets analyzed
}
```

## Usage Examples

### 1. Search Query Mode

Find code to refactor using a search query:

```powershell
$body = @{
    repo_dir = "C:\Users\57811\my-portfolio"
    query = "function component"
    focus = "readability"
    top_k = 3
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/refactor -Body $body -ContentType "application/json"
```

**Python:**
```python
import requests

response = requests.post(
    "http://127.0.0.1:5050/refactor",
    json={
        "repo_dir": "C:\\Users\\57811\\my-portfolio",
        "query": "function component",
        "focus": "readability",
        "top_k": 3
    }
)
print(response.json()["refactoring_suggestions"])
```

### 2. File Path Mode

Refactor a specific file:

```powershell
$body = @{
    repo_dir = "C:\Users\57811\my-portfolio"
    file_path = "src/components/Button.tsx"
    focus = "maintainability"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/refactor -Body $body -ContentType "application/json"
```

**Python:**
```python
import requests

response = requests.post(
    "http://127.0.0.1:5050/refactor",
    json={
        "repo_dir": "C:\\Users\\57811\\my-portfolio",
        "file_path": "src/components/Button.tsx",
        "focus": "maintainability"
    }
)
print(response.json()["refactoring_suggestions"])
```

### 3. Direct Code Snippets Mode

Provide code snippets directly:

```powershell
$codeSnippet = @"
def process_data(items):
    result = []
    for i in range(len(items)):
        item = items[i]
        if item > 0:
            result.append(item * 2)
    return result
"@

$body = @{
    code_snippets = @(
        @{
            file = "example.py"
            start = 1
            end = 10
            snippet = $codeSnippet
        }
    )
    focus = "readability and pythonic style"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/refactor -Body $body -ContentType "application/json"
```

**Python:**
```python
import requests

code_snippet = """
def process_data(items):
    result = []
    for i in range(len(items)):
        item = items[i]
        if item > 0:
            result.append(item * 2)
    return result
"""

response = requests.post(
    "http://127.0.0.1:5050/refactor",
    json={
        "code_snippets": [{
            "file": "example.py",
            "start": 1,
            "end": 10,
            "snippet": code_snippet.strip()
        }],
        "focus": "readability and pythonic style"
    }
)
print(response.json()["refactoring_suggestions"])
```

## Focus Areas

The `focus` parameter helps guide the refactoring suggestions:

- **"performance"** - Optimize for speed and efficiency
- **"readability"** - Improve code clarity and understandability
- **"maintainability"** - Make code easier to maintain and modify
- **"design patterns"** - Apply design patterns (SOLID, DRY, etc.)
- **"security"** - Address security concerns
- **"testability"** - Make code easier to test
- **Custom** - Any custom focus area (e.g., "reduce complexity", "error handling")

## Response Format

The `refactoring_suggestions` field contains markdown-formatted text with:

- **Issue**: Description of the problem
- **Before**: Original code snippet
- **After**: Refactored code snippet
- **Benefits**: Why the refactoring is better

Example output:

```markdown
## Refactoring Suggestions

### 1. Use List Comprehension

**Issue**: The loop can be simplified using Python list comprehension

**Before**:
```python
result = []
for i in range(len(items)):
    item = items[i]
    if item > 0:
        result.append(item * 2)
    else:
        result.append(0)
```

**After**:
```python
result = [item * 2 if item > 0 else 0 for item in items]
```

**Benefits**: 
- More concise and Pythonic
- Better performance
- Easier to read and understand
```

## Testing

Run the test script to try all three modes:

```powershell
python test_refactor.py
```

## Integration with VS Code Extension

The refactoring endpoint can be integrated into the VS Code extension by adding a new command:

```typescript
vscode.commands.registerCommand('code-assistant.refactor', async () => {
    // Get selected code or file
    // Call /refactor endpoint
    // Display suggestions in webview
});
```


# Multi-Repo Support Usage Guide

## Overview

The system now supports querying and indexing multiple repositories simultaneously. You can search across multiple codebases, ask questions that span multiple projects, and manage all your repositories from one interface.

---

## 🎯 Features

### 1. **Index Multiple Repositories**
Index multiple repositories at once with a single API call.

### 2. **Cross-Repo Search**
Search for code across multiple repositories simultaneously and get unified results.

### 3. **Multi-Repo Chat**
Ask questions about code that spans multiple repositories.

### 4. **Repository Management**
List all indexed repositories and their status.

---

## 📡 API Endpoints

### `GET /repos`
List all indexed repositories.

**Response:**
```json
{
  "ok": true,
  "repos": [
    {
      "repo_id": "my-portfolio",
      "repo_dir": "C:\\Users\\57811\\my-portfolio",
      "chunks": 19,
      "index_path": "data/index/my-portfolio/faiss.index"
    }
  ],
  "count": 1
}
```

**Example:**
```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:5050/repos
```

---

### `POST /index_repo` (Multi-Repo Mode)

Index multiple repositories at once.

**Request Body:**
```json
{
  "repo_dirs": [
    "C:\\Users\\57811\\repo1",
    "C:\\Users\\57811\\repo2",
    "C:\\Users\\57811\\repo3"
  ]
}
```

**Response:**
```json
{
  "ok": true,
  "repos": [
    {
      "repo_id": "repo1",
      "repo_dir": "C:\\Users\\57811\\repo1",
      "ok": true,
      "chunks": 150
    },
    {
      "repo_id": "repo2",
      "repo_dir": "C:\\Users\\57811\\repo2",
      "ok": true,
      "chunks": 200
    },
    {
      "repo_id": "repo3",
      "repo_dir": "C:\\Users\\57811\\repo3",
      "ok": false,
      "error": "Repository not found: ..."
    }
  ]
}
```

**Example (PowerShell):**
```powershell
$body = @{
    repo_dirs = @(
        "C:\Users\57811\my-portfolio",
        "C:\Users\57811\another-project"
    )
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/index_repo -Body $body -ContentType "application/json"
```

**Backward Compatible (Single Repo):**
The endpoint still supports single-repo mode with `repo_dir` parameter for backward compatibility.

---

### `POST /search` (Multi-Repo Mode)

Search across multiple repositories.

**Request Body:**
```json
{
  "repo_dirs": [
    "C:\\Users\\57811\\repo1",
    "C:\\Users\\57811\\repo2"
  ],
  "query": "authentication function",
  "k": 10
}
```

**Response:**
```json
{
  "ok": true,
  "results": [
    {
      "file": "C:\\Users\\57811\\repo1\\src\\auth.py",
      "start": 10,
      "end": 25,
      "snippet": "...",
      "score_vec": 0.85,
      "score_rg": 0.9,
      "repo_id": "repo1",
      "repo_dir": "C:\\Users\\57811\\repo1"
    },
    {
      "file": "C:\\Users\\57811\\repo2\\lib\\login.js",
      "start": 5,
      "end": 20,
      "snippet": "...",
      "score_vec": 0.82,
      "repo_id": "repo2",
      "repo_dir": "C:\\Users\\57811\\repo2"
    }
  ],
  "count": 2,
  "mode": "multi-repo",
  "repos_searched": 2
}
```

**Example (PowerShell):**
```powershell
$body = @{
    repo_dirs = @(
        "C:\Users\57811\my-portfolio",
        "C:\Users\57811\another-project"
    )
    query = "function component"
    k = 10
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/search -Body $body -ContentType "application/json"
```

**Backward Compatible (Single Repo):**
The endpoint still supports single-repo mode with `repo_dir` parameter.

---

### `POST /chat` (Multi-Repo Mode)

Ask questions across multiple repositories.

**Request Body:**
```json
{
  "repo_dirs": [
    "C:\\Users\\57811\\repo1",
    "C:\\Users\\57811\\repo2"
  ],
  "question": "How does authentication work across these projects?",
  "analysis_type": "explain",
  "top_k": 10
}
```

**Response:**
```json
{
  "ok": true,
  "answer": "Based on the code in both repositories...",
  "evidences": [
    {
      "file": "C:\\Users\\57811\\repo1\\src\\auth.py",
      "start": 10,
      "end": 25,
      "snippet": "...",
      "repo_id": "repo1"
    },
    {
      "file": "C:\\Users\\57811\\repo2\\lib\\login.js",
      "start": 5,
      "end": 20,
      "snippet": "...",
      "repo_id": "repo2"
    }
  ],
  "citations": [
    {
      "file": "C:\\Users\\57811\\repo1\\src\\auth.py",
      "start": 10,
      "end": 25,
      "repo_id": "repo1"
    }
  ],
  "repo_ids": ["repo1", "repo2"],
  "mode": "multi-repo"
}
```

**Example (PowerShell):**
```powershell
$body = @{
    repo_dirs = @(
        "C:\Users\57811\my-portfolio",
        "C:\Users\57811\another-project"
    )
    question = "What is the main structure of these projects?"
    analysis_type = "explain"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/chat -Body $body -ContentType "application/json"
```

**Backward Compatible (Single Repo):**
The endpoint still supports single-repo mode with `repo_dir` parameter.

---

## 💡 Use Cases

### 1. **Cross-Project Code Discovery**
Find similar patterns or implementations across multiple projects:
```json
{
  "repo_dirs": ["project-a", "project-b", "project-c"],
  "query": "error handling pattern"
}
```

### 2. **Multi-Project Analysis**
Ask questions that span multiple codebases:
```json
{
  "repo_dirs": ["backend", "frontend", "shared"],
  "question": "How is state management implemented across these projects?"
}
```

### 3. **Code Review Across Projects**
Review code patterns across multiple repositories:
```json
{
  "repo_dirs": ["legacy-app", "new-app"],
  "question": "What are the differences in API design between these projects?"
}
```

### 4. **Documentation Generation**
Generate documentation that covers multiple projects:
```json
{
  "repo_dirs": ["api", "sdk", "docs"],
  "question": "Generate a comprehensive API documentation guide"
}
```

---

## 🔧 How It Works

### Search Across Repositories

1. **Parallel Search**: Each repository is searched independently
2. **Result Merging**: Results from all repositories are combined and ranked
3. **Score Normalization**: Results are scored consistently across repositories
4. **Repo Identification**: Each result includes `repo_id` and `repo_dir` for tracking

### Result Ranking

Results are ranked by:
1. **Vector similarity score**: Semantic match quality
2. **Keyword match score**: Text match quality  
3. **Cross-repo bonus**: Boost for matches found in multiple repos

### Index Management

- Each repository maintains its own FAISS index
- Indexes are stored in separate directories: `data/index/{repo_id}/`
- Auto-sync works independently for each repository
- No conflicts between repositories

---

## 📊 Response Format

### Single-Repo Mode
```json
{
  "mode": "single-repo",
  "repo_id": "my-portfolio",
  ...
}
```

### Multi-Repo Mode
```json
{
  "mode": "multi-repo",
  "repo_ids": ["repo1", "repo2"],
  "repos_searched": 2,
  ...
}
```

All results include `repo_id` field to identify the source repository.

---

## ⚠️ Important Notes

1. **All repos must be indexed**: Repositories must be indexed before searching. Use `/index_repo` with `repo_dirs` to index multiple at once.

2. **Performance**: Searching multiple repositories takes longer than single-repo search. Results are merged and sorted, which adds processing time.

3. **Auto-sync**: Each repository is watched independently. File changes in one repo don't affect others.

4. **Backward compatibility**: All endpoints still support single-repo mode with `repo_dir` parameter.

5. **Repo ID format**: Repository IDs are generated from directory names. Make sure directory names are unique or use full paths.

---

## 🧪 Testing

Run the test script to verify multi-repo support:

```powershell
python test_multi_repo.py
```

Make sure to update `TEST_REPOS` list in the test script with your repository paths.

---

## 📝 Examples

### Example 1: Index Two Repositories

```powershell
$body = @{
    repo_dirs = @(
        "C:\Users\57811\my-portfolio",
        "C:\Users\57811\smartcursor"
    )
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/index_repo -Body $body -ContentType "application/json"
```

### Example 2: Search Across Repositories

```powershell
$body = @{
    repo_dirs = @(
        "C:\Users\57811\my-portfolio",
        "C:\Users\57811\smartcursor"
    )
    query = "Flask application"
    k = 5
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/search -Body $body -ContentType "application/json"
```

### Example 3: Chat Across Repositories

```powershell
$body = @{
    repo_dirs = @(
        "C:\Users\57811\my-portfolio",
        "C:\Users\57811\smartcursor"
    )
    question = "How are REST APIs implemented in these projects?"
    analysis_type = "explain"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/chat -Body $body -ContentType "application/json"
```

---

## 🎯 Benefits

1. **Unified Search**: Find code patterns across all your projects
2. **Cross-Project Learning**: Understand how similar problems are solved differently
3. **Better Organization**: Manage multiple repositories from one interface
4. **Consistent Experience**: Same search and chat experience across all repos
5. **Efficient Workflow**: No need to switch between repositories

---

*Last Updated: November 2025*


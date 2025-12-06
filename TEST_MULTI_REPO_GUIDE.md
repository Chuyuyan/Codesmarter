# Multi-Repo Support Testing Guide

## ✅ Syntax Check
The code syntax is valid - no Python errors!

## 🧪 Testing Steps

### Step 1: Start the Server
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Start server
python -m backend.app
```

### Step 2: Test List Repos Endpoint
```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:5050/repos
```

**Expected:** Should return list of indexed repositories (may be empty initially)

---

### Step 3: Test Index Multiple Repos
```powershell
# Update paths to your actual repositories
$body = @{
    repo_dirs = @(
        "C:\Users\57811\my-portfolio",
        "C:\Users\57811\smartcursor"  # Or another repo you have
    )
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/index_repo -Body $body -ContentType "application/json"
```

**Expected:** Should index both repositories and return results for each

**Check server console for:**
- `[index_repo] Indexing 2 repositories...`
- `[index_repo] Indexed repo1: X chunks`
- `[index_repo] Indexed repo2: Y chunks`

---

### Step 4: Test List Repos Again
```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:5050/repos
```

**Expected:** Should now show both repositories in the list

---

### Step 5: Test Search Across Repos
```powershell
$body = @{
    repo_dirs = @(
        "C:\Users\57811\my-portfolio",
        "C:\Users\57811\smartcursor"
    )
    query = "function component"  # Or any search query
    k = 5
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/search -Body $body -ContentType "application/json"
```

**Expected:** Should return results from both repositories, each with `repo_id` field

**Check response:**
- `mode: "multi-repo"`
- `repos_searched: 2`
- Results should have `repo_id` and `repo_dir` fields

---

### Step 6: Test Chat Across Repos
```powershell
$body = @{
    repo_dirs = @(
        "C:\Users\57811\my-portfolio",
        "C:\Users\57811\smartcursor"
    )
    question = "What is the main structure of these projects?"
    analysis_type = "explain"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/chat -Body $body -ContentType "application/json"
```

**Expected:** Should return answer that references code from both repositories

**Check response:**
- `mode: "multi-repo"`
- `repo_ids: ["my-portfolio", "smartcursor"]` (or your repo names)
- Evidences should have `repo_id` field

---

## 🐛 Troubleshooting

### Error: "repo_id_from_path is not defined"
**Fix:** Make sure you're importing from `multi_repo` module. The imports should be correct.

### Error: "Repository not indexed"
**Fix:** Index the repositories first using `/index_repo` with `repo_dirs` array.

### Error: "repo_dirs must be a list"
**Fix:** In PowerShell, use array syntax: `@("path1", "path2")`

### Results show only one repo
**Fix:** Check that both repositories are indexed and search query is relevant to both.

---

## ✅ Success Criteria

1. **List Repos:** Should return all indexed repositories
2. **Index Multiple:** Should index all repos and return success for each
3. **Search Multiple:** Should return results from all repos with `repo_id` field
4. **Chat Multiple:** Should generate answer using code from multiple repos

---

## 📝 Quick Test Checklist

- [ ] Server starts without errors
- [ ] `/repos` endpoint returns list
- [ ] Index multiple repos works
- [ ] Search across repos returns results with `repo_id`
- [ ] Chat across repos works and shows multiple `repo_ids` in response
- [ ] Results are correctly merged and sorted
- [ ] Backward compatibility: single-repo mode still works

---

*Once you run these tests, we can verify everything is working correctly!*


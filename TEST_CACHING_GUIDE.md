# Testing Caching System - Step by Step Guide

## Option 1: Quick Test (No Interaction Required)

Run the simple test script:

```bash
python test_caching_simple.py
```

This will test all endpoints without asking for input.

---

## Option 2: Full Test (With Cache Population)

To see caching actually work (cache hits), you need to populate the cache first.

### Step 1: Populate the Cache

Make some API calls to populate the cache:

#### A. Test LLM Response Caching (Chat Endpoint)

```bash
# First call - will be cached
$body = @{
    repo_dir = "C:\Users\57811\my-portfolio"  # Your repo path
    question = "What is the main function in this codebase?"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/chat -Body $body -ContentType "application/json"

# Second call - should use cache (faster!)
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/chat -Body $body -ContentType "application/json"
```

#### B. Test Search Result Caching

```bash
# First search - will be cached
$body = @{
    repo_dir = "C:\Users\57811\my-portfolio"  # Your repo path
    query = "function"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/search -Body $body -ContentType "application/json"

# Second search - should use cache (faster!)
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/search -Body $body -ContentType "application/json"
```

#### C. Test Refactoring Caching

```bash
# First refactor - will be cached
$body = @{
    repo_dir = "C:\Users\57811\my-portfolio"  # Your repo path
    file_path = "app.py"  # A file in your repo
    focus = "readability"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/refactor -Body $body -ContentType "application/json"

# Second refactor - should use cache (faster!)
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/refactor -Body $body -ContentType "application/json"
```

### Step 2: Check Cache Statistics

```bash
# Check if cache has entries now
curl http://127.0.0.1:5050/cache/stats

# Or in PowerShell:
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:5050/cache/stats
```

You should see:
- `total_entries` > 0
- `hits` and `misses` counts
- `hit_rate` percentage

### Step 3: Run Full Test

Now run the test script:

```bash
python test_caching.py
```

**What to enter:**

1. **Repository directory:**
   ```
   C:\Users\57811\my-portfolio
   ```
   (Or your actual repository path)

2. **Search query:**
   ```
   function
   ```
   (Or any search term - same as you used in Step 1B)

3. **Clear all caches?**
   ```
   n
   ```
   (Press Enter or type 'n' to skip - unless you want to clear)

### Step 4: Verify Cache Hits

The test output should show:
- ✅ **First search:** `Cached: False` (cache MISS)
- ✅ **Second search:** `Cached: True` (cache HIT)
- ⚡ **Speedup:** Should show faster response time

---

## Option 3: Visual Verification (Recommended)

### Step 1: Check Cache Before Use

```bash
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:5050/cache/stats
```

Expected: `total_entries: 0` (empty)

### Step 2: Make API Calls

Make 2-3 chat/search/refactor calls (see Option 2 above).

### Step 3: Check Cache After Use

```bash
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:5050/cache/stats
```

Expected: `total_entries > 0`, shows hits/misses

### Step 4: Make Same Call Again

Make the exact same API call again.

**Expected Results:**
- ✅ **Response time:** Much faster (cache hit)
- ✅ **Cache stats:** `hits` count increased
- ✅ **Hit rate:** Increased percentage

---

## What to Expect

### First Run (Empty Cache)
```
total_entries: 0
hits: 0
misses: 0
hit_rate: 0.0%
```

### After API Calls (Cache Populated)
```
total_entries: 5-20 (depends on usage)
hits: 0-10 (if you repeated queries)
misses: 5-20 (first-time queries)
hit_rate: 0-50% (depends on repetitions)
```

### After Repeated Queries (Cache Working)
```
total_entries: 10-30
hits: 10-50 (repeated queries use cache)
misses: 10-30 (new queries)
hit_rate: 30-70% (good hit rate!)
```

---

## Quick Test Commands

### Test Cache Stats
```bash
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:5050/cache/stats
```

### Test Cache Cleanup
```bash
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/cache/cleanup
```

### Test Cache Clear
```bash
$body = @{ cache_type = "all" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/cache/clear -Body $body -ContentType "application/json"
```

---

## Troubleshooting

### Cache Still Empty After API Calls?

**Check:**
1. ✅ Server is running: `python -m backend.app`
2. ✅ API calls are successful (check response)
3. ✅ Cache directory exists: `data/cache/`
4. ✅ Check server logs for cache messages:
   - `[llm_api] Cache HIT for...`
   - `[llm_api] Cache MISS for...`
   - `[search] Cache HIT for query...`
   - `[search] Cache MISS for query...`

### Cache Hit Rate Low?

**Normal for:**
- First-time usage (all queries are new)
- Diverse queries (few repetitions)
- Frequently changing codebase

**Expected:**
- 30-60% hit rate for LLM responses (repeated questions)
- 40-70% hit rate for search results (same queries)

---

## Summary

**Simplest Test:**
```bash
python test_caching_simple.py
```

**Full Test (to see cache working):**
1. Populate cache (make API calls)
2. Check stats: `GET /cache/stats`
3. Make same calls again (should be faster)
4. Check stats again (hits should increase)

**What to Enter in Interactive Test:**
- Repository: `C:\Users\57811\my-portfolio` (your repo path)
- Query: `function` (or any search term)
- Clear caches: `n` (skip unless needed)


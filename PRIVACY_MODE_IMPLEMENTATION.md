# Privacy Mode Implementation

## Overview

Privacy mode ensures GDPR compliance and security for privacy-conscious users. When enabled, no code is stored in indexes or caches.

**Status:** ✅ **COMPLETE**

---

## Features Implemented

### 1. **Privacy Mode Configuration** ✅
- Environment variable: `PRIVACY_MODE=true` in `.env`
- Runtime enable/disable via API endpoints
- Singleton pattern for consistent state

### 2. **Indexing Control** ✅
- Indexing blocked when privacy mode enabled
- Returns 403 (Forbidden) with clear error message
- Prevents code storage in FAISS indexes

### 3. **Caching Control** ✅
- Caching disabled when privacy mode enabled
- LLM response cache skipped
- Search result cache skipped
- No code stored in any cache

### 4. **GDPR Compliance** ✅
- Clear all data endpoint (`/privacy/clear`)
- Removes all indexes and caches
- Right to be forgotten compliance

### 5. **Privacy Status** ✅
- Status endpoint shows current privacy mode state
- Statistics on stored data (when disabled)
- Clear indication of what's allowed/blocked

---

## API Endpoints

### `GET /privacy/status`
Get privacy mode status and statistics.

**Response:**
```json
{
  "ok": true,
  "enabled": false,
  "indexing_allowed": true,
  "caching_allowed": true,
  "code_storage_allowed": true,
  "stored_data": {
    "indexed_repositories": 2,
    "cached_entries": 150
  }
}
```

### `POST /privacy/enable`
Enable privacy mode (runtime).

**Response:**
```json
{
  "ok": true,
  "message": "Privacy mode enabled",
  "enabled": true,
  "note": "No code will be stored in indexes or caches"
}
```

### `POST /privacy/disable`
Disable privacy mode (runtime).

**Response:**
```json
{
  "ok": true,
  "message": "Privacy mode disabled",
  "enabled": false,
  "note": "Code will be indexed and cached normally"
}
```

### `POST /privacy/clear`
Clear all stored data (indexes, caches) when privacy mode is enabled.

**Response:**
```json
{
  "ok": true,
  "message": "All data cleared successfully",
  "indexes_cleared": 2,
  "caches_cleared": 3,
  "total_files_removed": 250
}
```

**Note:** Only works when privacy mode is enabled (safety check).

---

## Configuration

### Environment Variable

Add to `.env`:
```bash
PRIVACY_MODE=true
```

### Runtime Configuration

Enable/disable via API:
```bash
# Enable
curl -X POST http://127.0.0.1:5050/privacy/enable

# Disable
curl -X POST http://127.0.0.1:5050/privacy/disable
```

---

## Behavior When Privacy Mode Enabled

### Indexing (`/index_repo`)
- **Blocked:** Returns 403 Forbidden
- **Error Message:** "Privacy mode is enabled. Indexing is not allowed."
- **Suggestion:** Use local-only processing

### Caching
- **LLM Cache:** Skipped (no responses cached)
- **Search Cache:** Skipped (no results cached)
- **Embeddings Cache:** Skipped (no embeddings cached)

### Code Storage
- **FAISS Indexes:** Not created
- **Cache Files:** Not written
- **Metadata:** Not stored

### Search & Chat
- **Still Works:** Search and chat still function
- **No Storage:** Results not cached
- **No Index:** Requires existing indexes (if any)

---

## Integration Points

### Backend (`backend/app.py`)

**Indexing Endpoint:**
```python
privacy_mode = get_privacy_mode()
if not privacy_mode.should_index():
    return jsonify({
        "ok": False,
        "error": "Privacy mode is enabled. Indexing is not allowed."
    }), 403
```

**Search Endpoint:**
```python
privacy_mode = get_privacy_mode()
use_search_cache = privacy_mode.should_cache()

if use_search_cache:
    # Cache search results
    search_cache.set(query, repo_dir, results)
else:
    print("Privacy mode enabled - not caching results")
```

### LLM API (`backend/modules/llm_api.py`)

**Caching Control:**
```python
if is_privacy_mode_enabled():
    use_cache = False
    print("Privacy mode enabled - skipping cache")
```

---

## Use Cases

### 1. **Enterprise/Compliance**
- Enable privacy mode for sensitive codebases
- Ensure no code leaves the organization
- GDPR compliance for EU customers

### 2. **Security-Conscious Users**
- Privacy-first development
- No code storage in indexes
- Local-only processing

### 3. **Temporary Privacy**
- Enable for specific operations
- Disable when privacy not required
- Runtime control via API

### 4. **Data Cleanup**
- Clear all stored data on demand
- Right to be forgotten (GDPR)
- Complete data removal

---

## Testing

### Test Privacy Mode Status

```bash
curl http://127.0.0.1:5050/privacy/status
```

### Test Indexing Block

```bash
# Enable privacy mode
curl -X POST http://127.0.0.1:5050/privacy/enable

# Try to index (should fail)
curl -X POST http://127.0.0.1:5050/index_repo \
  -d '{"repo_dir": "/path/to/repo"}'

# Response: 403 Forbidden
```

### Test Cache Disable

```bash
# Enable privacy mode
curl -X POST http://127.0.0.1:5050/privacy/enable

# Make search (should work but not cache)
curl -X POST http://127.0.0.1:5050/search \
  -d '{"repo_dir": "/path/to/repo", "query": "function"}'

# Check cache stats (should be empty)
curl http://127.0.0.1:5050/cache/stats
```

### Test Data Clear

```bash
# Enable privacy mode
curl -X POST http://127.0.0.1:5050/privacy/enable

# Clear all data
curl -X POST http://127.0.0.1:5050/privacy/clear

# Response shows what was cleared
```

---

## Benefits

### 1. **GDPR Compliance** 📋
- Right to be forgotten
- No code storage without consent
- Complete data removal capability

### 2. **Security** 🔒
- No code leaves the system
- Local-only processing option
- Enterprise-ready security

### 3. **Privacy** 🔐
- Privacy-first approach
- User control over data
- Transparent privacy settings

### 4. **Flexibility** ⚙️
- Runtime enable/disable
- Per-operation control
- Easy configuration

---

## Limitations

### When Privacy Mode Enabled:

1. **No Indexing:** Cannot index new repositories
2. **No Caching:** All caching disabled (slower responses)
3. **No Persistence:** No code stored between sessions
4. **Search Limitations:** Requires existing indexes (if any)

### Workarounds:

1. **Local-Only Processing:** Process code without storing
2. **Temporary Disable:** Disable for indexing, re-enable after
3. **In-Memory Only:** Use system without persistence

---

## Future Enhancements

### Potential Improvements:

1. **Selective Privacy:** Privacy mode per repository
2. **Privacy Levels:** Different privacy levels (strict, moderate, relaxed)
3. **Audit Logging:** Track privacy mode changes
4. **Data Encryption:** Encrypt stored data even when privacy disabled
5. **Privacy Dashboard:** Visual privacy settings and data overview

---

## Summary

✅ **Privacy mode is fully implemented and operational**

**Key Features:**
- Environment variable configuration
- Runtime enable/disable
- Indexing blocked when enabled
- Caching disabled when enabled
- GDPR compliance (clear all data)
- Privacy status endpoint

**Integration:**
- `/index_repo` - Privacy check
- `/search` - Cache control
- LLM calls - Cache control
- All endpoints respect privacy mode

**Production Ready:** ✅ Yes

---

*Last Updated: Current Implementation Status*


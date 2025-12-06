# Privacy Mode Improvement

## Problem
Previously, when privacy mode was enabled:
- **Indexing was completely blocked** - users couldn't use the system at all
- **Caching was disabled** - making the system slower with no benefits
- **Made the system unusable** for privacy-conscious users

## Solution
Privacy mode now uses **in-memory storage (RAM only)** instead of blocking functionality:
- ✅ **All features work normally** (indexing, caching, search, chat)
- ✅ **No disk writes** - everything stored in RAM
- ✅ **Auto-cleanup on shutdown** - data cleared when server stops
- ✅ **Manual cleanup available** - users can clear data anytime

## How It Works

### When Privacy Mode is Enabled:
1. **Indexes** are stored in RAM only (no `data/index/` files written)
2. **Caches** are stored in RAM only (no `data/cache/` files written)
3. **Auto-cleanup** on server shutdown (data cleared automatically)
4. **Manual cleanup** via `/privacy/clear` endpoint

### When Privacy Mode is Disabled (Default):
- Normal disk-based storage (`data/index/`, `data/cache/`)
- Data persists across server restarts
- Manual cleanup available but data persists until cleared

## Implementation Details

### Changes Made:

1. **`backend/modules/privacy.py`**:
   - `should_index()`, `should_cache()`, `should_store_code()` now return `True` always
   - Added `use_in_memory_storage()` method to check storage type
   - Updated `clear_all_data()` to handle both in-memory and disk cleanup
   - Updated `get_status()` to show storage type (in-memory vs disk)

2. **`backend/modules/vector_store.py`**:
   - Added `in_memory` parameter to `FaissStore.__init__()`
   - When `in_memory=True`, indexes are kept in RAM only (no disk writes)
   - Global registry `_in_memory_stores` tracks all in-memory indexes

3. **`backend/modules/cache.py`**:
   - Added `in_memory` parameter to `Cache.__init__()`
   - Added `in_memory` parameter to `LLMResponseCache`, `SearchResultCache`, `EmbeddingCache`
   - When `in_memory=True`, caches are kept in RAM only (no disk writes)
   - Global registry `_in_memory_caches` tracks all in-memory caches
   - Cache getter functions (`get_llm_cache()`, etc.) auto-detect privacy mode

4. **`backend/app.py`**:
   - Removed blocking logic for privacy mode (no more 403 errors)
   - Indexing now uses `in_memory=True` when privacy mode enabled
   - Added `cleanup_privacy_mode()` function for auto-cleanup on shutdown
   - Registered cleanup with `atexit` handler

## API Endpoints

### Get Privacy Status
```bash
GET /privacy/status
```
Returns:
```json
{
  "ok": true,
  "enabled": true,
  "storage_type": "in-memory (RAM)",
  "indexing_allowed": true,
  "caching_allowed": true,
  "auto_cleanup": "On server shutdown",
  "stored_data": {
    "indexed_repositories": 2,
    "cached_entries": 5,
    "location": "RAM (in-memory)",
    "note": "Data cleared automatically on server shutdown"
  }
}
```

### Enable Privacy Mode
```bash
POST /privacy/enable
```

### Disable Privacy Mode
```bash
POST /privacy/disable
```

### Clear All Data
```bash
POST /privacy/clear
```
- If privacy mode enabled: clears in-memory data only
- If privacy mode disabled: clears disk-based data

## Benefits

1. **Usability**: Privacy-conscious users can now use all features
2. **Security**: No disk storage when privacy mode enabled
3. **Performance**: Still get caching benefits (in RAM)
4. **Compliance**: GDPR-friendly - data cleared on shutdown
5. **Flexibility**: Users can switch between modes anytime

## Usage

### Enable Privacy Mode
```bash
# Via environment variable
export PRIVACY_MODE=true

# Or via API
curl -X POST http://127.0.0.1:5050/privacy/enable
```

### Use System Normally
With privacy mode enabled, all features work:
- Index repositories (stored in RAM)
- Search code (uses in-memory index)
- Chat with AI (uses in-memory cache)
- Generate tests/docs (uses in-memory cache)

### Data Auto-Cleared
When server shuts down (Ctrl+C or crash):
- All in-memory indexes cleared
- All in-memory caches cleared
- No data left behind

### Manual Cleanup (Optional)
```bash
curl -X POST http://127.0.0.1:5050/privacy/clear
```

## Testing

1. **Enable privacy mode**:
   ```bash
   export PRIVACY_MODE=true
   python -m backend.app
   ```

2. **Index a repository**:
   ```bash
   curl -X POST http://127.0.0.1:5050/index_repo \
     -H "Content-Type: application/json" \
     -d '{"repo_dir": "/path/to/repo"}'
   ```
   ✅ Should work (stored in RAM, not disk)

3. **Check privacy status**:
   ```bash
   curl http://127.0.0.1:5050/privacy/status
   ```
   ✅ Should show `"storage_type": "in-memory (RAM)"`

4. **Stop server** (Ctrl+C)
   ✅ Should see cleanup message: "Cleared X indexes and Y caches"

5. **Verify no disk data**:
   ```bash
   ls data/index/  # Should be empty or contain old data only
   ls data/cache/  # Should be empty or contain old data only
   ```

## Notes

- **Memory Usage**: In-memory storage uses RAM, so very large repositories may consume significant memory
- **Persistence**: Data is lost on server restart when privacy mode enabled
- **Performance**: In-memory storage is actually faster than disk (no I/O)
- **Compatibility**: All existing endpoints work the same, just storage location changes


# Streaming Debug Guide

## Issue
Code window opens but code doesn't appear in real-time during streaming.

## Potential Causes

1. **Backend not sending chunks properly**
   - Check server logs for streaming errors
   - Verify SSE format is correct

2. **VS Code extension not parsing SSE correctly**
   - Check Developer Console for errors
   - Look for `[generateTests]` logs

3. **Editor updates happening too fast**
   - Added batching (updates every 100ms or every 5 chunks)
   - Added proper initialization delay

4. **Document not ready**
   - Added 100ms delay after opening document
   - Ensure document is visible before streaming

## Debug Steps

### 1. Check Developer Console
- Press `Ctrl+Shift+P` → "Developer: Toggle Developer Tools"
- Open Console tab
- Look for:
  - `[generateTests] Starting streaming request...`
  - `[generateTests] Received SSE event: start`
  - `[generateTests] Received SSE event: chunk`
  - `[generateTests] Received SSE event: done`
  - Any errors or warnings

### 2. Check Backend Logs
- Look for:
  - `[generate_tests] Generating unit tests (stream=True)...`
  - `[test_generation] Streaming unit tests...`
  - Any errors in streaming

### 3. Test Backend Directly
```powershell
# Test if streaming works at backend level
$body = @{
    code_snippet = "def test():`n    pass"
    repo_dir = "C:\Users\57811\my-portfolio"
    test_type = "unit"
    stream = $true
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:5050/generate_tests" -Body $body -ContentType "application/json" -TimeoutSec 180
```

## What Was Fixed

1. ✅ Added batching for editor updates (not every chunk)
2. ✅ Added proper document initialization delay
3. ✅ Added comprehensive logging
4. ✅ Added error handling for editor edits
5. ✅ Ensure final update happens even if stream ends unexpectedly
6. ✅ Handle empty lines in SSE parsing

## If Still Not Working

1. Check if backend is actually streaming (test with curl or PowerShell)
2. Check Developer Console for errors
3. Try non-streaming mode first to verify basic functionality
4. Check if document is visible and focused
5. Verify extension was reloaded after changes


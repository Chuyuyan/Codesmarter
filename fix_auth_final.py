#!/usr/bin/env python3
# Fix auth.js in Docker container

import sys

file_path = '/app/static/js/auth.js'

# Read file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"File size: {len(content)} characters")
print(f"First 200 chars: {content[:200]}\n")

# Find the exact line to replace
old_line = "const API_BASE = 'http://127.0.0.1:5050';"
new_code = """// Auto-detect API base URL based on current page
const API_BASE = (() => {
    if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {
        return '';
    }
    return 'http://127.0.0.1:5050';
})();"""

if old_line in content:
    content = content.replace(old_line, new_code)
    print("✓ Replaced API_BASE definition")
else:
    print("⚠ Exact line not found, checking variations...")
    # Try with different spacing
    variations = [
        'const API_BASE = "http://127.0.0.1:5050";',
        "const API_BASE='http://127.0.0.1:5050';",
        'const API_BASE = \'http://127.0.0.1:5050\';',
    ]
    replaced = False
    for var in variations:
        if var in content:
            content = content.replace(var, new_code)
            print(f"✓ Replaced variation: {var[:30]}...")
            replaced = True
            break
    
    if not replaced:
        # Try to find line number 6
        lines = content.split('\n')
        if len(lines) > 6 and 'API_BASE' in lines[5] and '127.0.0.1' in lines[5]:
            lines[5] = "// Auto-detect API base URL based on current page"
            lines.insert(6, "const API_BASE = (() => {")
            lines.insert(7, "    if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {")
            lines.insert(8, "        return '';")
            lines.insert(9, "    }")
            lines.insert(10, "    return 'http://127.0.0.1:5050';")
            lines.insert(11, "})();")
            content = '\n'.join(lines)
            print("✓ Replaced line 6 manually")
        else:
            print("✗ Could not find API_BASE line to replace")
            sys.exit(1)

# Fix URL construction
url_pattern = '        const url = `${API_BASE}${endpoint}`;'
if url_pattern in content and 'Use relative path' not in content:
    new_url = '        // Use relative path if API_BASE is empty (same origin), otherwise use full URL\n        const url = API_BASE ? `${API_BASE}${endpoint}` : endpoint;'
    content = content.replace(url_pattern, new_url)
    print("✓ Updated URL construction")

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ File saved successfully!")
print(f"\nFirst 25 lines of updated file:")
print('\n'.join(content.split('\n')[:25]))


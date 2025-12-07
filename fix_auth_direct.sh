#!/bin/bash
# Direct fix for auth.js in container

echo "Fixing auth.js in container..."

# Use Python with a simpler approach
docker exec smartcursor python3 -c "
import re

file_path = '/app/static/js/auth.js'

# Read file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f'File size: {len(content)} chars')

# Find and replace API_BASE line
old_line = \"const API_BASE = 'http://127.0.0.1:5050';\"
new_lines = '''// Auto-detect API base URL based on current page
const API_BASE = (() => {
    if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {
        return '';
    }
    return 'http://127.0.0.1:5050';
})();'''

if old_line in content:
    # Replace the line (handle with/without surrounding context)
    content = content.replace(old_line, new_lines)
    print('✓ Replaced API_BASE definition')
else:
    print('⚠ Old pattern not found, trying regex...')
    pattern = r\"const API_BASE = 'http://127\\.0\\.0\\.1:5050';\"
    if re.search(pattern, content):
        content = re.sub(pattern, new_lines, content)
        print('✓ Replaced using regex')
    elif 'Auto-detect API base URL' in content:
        print('✓ File already has auto-detect logic')
    else:
        print('⚠ Could not find API_BASE pattern')

# Fix URL construction
if 'const url = \`\${API_BASE}\${endpoint}\`;' in content and 'Use relative path' not in content:
    old_url = '        const url = \`\${API_BASE}\${endpoint}\`;'
    new_url = '        // Use relative path if API_BASE is empty (same origin), otherwise use full URL\n        const url = API_BASE ? \`\${API_BASE}\${endpoint}\` : endpoint;'
    content = content.replace(old_url, new_url)
    print('✓ Updated URL construction')

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ File saved successfully')
"

echo ""
echo "Verifying..."
docker exec smartcursor head -20 /app/static/js/auth.js


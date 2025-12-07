#!/bin/bash
# Simple fix using sed - line by line replacement

echo "Fixing auth.js using sed..."

# Backup first
docker exec smartcursor cp /app/static/js/auth.js /app/static/js/auth.js.bak

# Replace line 6-14 (the API_BASE section)
docker exec smartcursor bash -c "
cat > /tmp/fix_auth.py << 'PYTHON'
import sys

file_path = '/app/static/js/auth.js'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with API_BASE
new_lines = []
i = 0
while i < len(lines):
    if 'const API_BASE' in lines[i] and 'http://127.0.0.1:5050' in lines[i]:
        # Replace with new code
        new_lines.append('// Auto-detect API base URL based on current page\n')
        new_lines.append('const API_BASE = (() => {\n')
        new_lines.append('    if (window.location.hostname !== \"127.0.0.1\" && window.location.hostname !== \"localhost\") {\n')
        new_lines.append('        return \"\";\n')
        new_lines.append('    }\n')
        new_lines.append('    return \"http://127.0.0.1:5050\";\n')
        new_lines.append('})();\n')
        i += 1
        # Skip the old line
        continue
    elif 'const url = \`\${API_BASE}\${endpoint}\`;' in lines[i]:
        # Fix URL construction
        new_lines.append('        // Use relative path if API_BASE is empty (same origin), otherwise use full URL\n')
        new_lines.append('        const url = API_BASE ? \`\${API_BASE}\${endpoint}\` : endpoint;\n')
        i += 1
        continue
    else:
        new_lines.append(lines[i])
    i += 1

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('✓ File updated')
PYTHON

python3 /tmp/fix_auth.py
"

echo ""
echo "Verifying fix..."
docker exec smartcursor head -25 /app/static/js/auth.js


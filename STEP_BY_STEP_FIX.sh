#!/bin/bash
# Step by step fix - run each command separately

echo "Step 1: Creating fix script..."
python3 << 'PYEOF' > /tmp/fix_auth.py
import sys

file_path = '/app/static/js/auth.js'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    if 'const API_BASE' in lines[i] and '127.0.0.1' in lines[i]:
        new_lines.append("// Auto-detect API base URL based on current page\n")
        new_lines.append("const API_BASE = (() => {\n")
        new_lines.append("    if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {\n")
        new_lines.append("        return '';\n")
        new_lines.append("    }\n")
        new_lines.append("    return 'http://127.0.0.1:5050';\n")
        new_lines.append("})();\n")
        i += 1
        continue
    elif 'const url = `${API_BASE}${endpoint}`;' in lines[i] and 'Use relative path' not in ''.join(new_lines[-5:]):
        new_lines.append("        // Use relative path if API_BASE is empty\n")
        new_lines.append("        const url = API_BASE ? `${API_BASE}${endpoint}` : endpoint;\n")
        i += 1
        continue
    new_lines.append(lines[i])
    i += 1

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✓ File fixed!")
PYEOF

echo "Step 2: Copying script to container..."
docker cp /tmp/fix_auth.py smartcursor:/tmp/fix_auth.py

echo "Step 3: Running fix in container..."
docker exec smartcursor python3 /tmp/fix_auth.py

echo "Step 4: Verifying..."
docker exec smartcursor head -20 /app/static/js/auth.js


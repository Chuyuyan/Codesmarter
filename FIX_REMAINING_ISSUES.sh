#!/bin/bash
# Fix remaining issues: remove <br/> tag and fix indentation

echo "Fixing <br/> tag and indentation..."

# Fix in container
docker exec smartcursor python3 << 'PYEOF'
file_path = '/app/static/js/auth.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove <br/> tags
content = content.replace('<br/>', '')
content = content.replace('<br>', '')

# Fix indentation for the API_BASE block (convert tabs to spaces)
lines = content.split('\n')
new_lines = []
for i, line in enumerate(lines):
    # Fix the API_BASE block indentation (lines around the auto-detect code)
    if '// Auto-detect API base URL' in line:
        new_lines.append('// Auto-detect API base URL based on current page')
    elif 'const API_BASE = (() => {' in line and line.startswith('\t'):
        new_lines.append('const API_BASE = (() => {')
    elif 'if (window.location.hostname' in line and '\t' in line[:8]:
        new_lines.append('    if (window.location.hostname !== \'127.0.0.1\' && window.location.hostname !== \'localhost\') {')
    elif 'return \'\';' in line and '\t' in line[:12]:
        new_lines.append('        return \'\';')
    elif line.strip() == '}' and i > 0 and 'return' in lines[i-1]:
        new_lines.append('    }')
    elif 'return \'http://127.0.0.1:5050\';' in line and '\t' in line[:8]:
        new_lines.append('    return \'http://127.0.0.1:5050\';')
    elif '})();' in line and '\t' in line[:4]:
        new_lines.append('})();')
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed <br/> tags and indentation!")
PYEOF

echo ""
echo "Verifying fix..."
docker exec smartcursor head -20 /app/static/js/auth.js


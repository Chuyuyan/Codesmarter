#!/bin/bash
# Script to fix auth.js in Docker container using sed

echo "Fixing auth.js in container..."

# First, let's check if the file exists
echo "Checking file..."
docker exec smartcursor ls -la /app/static/js/auth.js

# Create a backup
echo "Creating backup..."
docker exec smartcursor cp /app/static/js/auth.js /app/static/js/auth.js.backup

# Read the current file to see what we're working with
echo ""
echo "Current file content (first 10 lines):"
docker exec smartcursor head -10 /app/static/js/auth.js

# Fix using a Python script inside the container
echo ""
echo "Applying fix..."
docker exec smartcursor python3 << 'PYTHON_SCRIPT'
import re

file_path = '/app/static/js/auth.js'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the API_BASE line
    # Pattern 1: Simple assignment
    pattern1 = r"const API_BASE = 'http://127\.0\.0\.1:5050';"
    replacement = """// Auto-detect API base URL based on current page
const API_BASE = (() => {
    if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {
        return '';
    }
    return 'http://127.0.0.1:5050';
})();"""
    
    if re.search(pattern1, content):
        content = re.sub(pattern1, replacement, content)
        print("✓ Found and replaced pattern 1")
    else:
        # Pattern 2: Already has auto-detect? Check if it needs updating
        if 'Auto-detect API base URL' in content:
            print("✓ File already has auto-detect logic")
        else:
            # Pattern 3: Try to find API_BASE anywhere
            if 'const API_BASE' in content:
                # Replace the first occurrence
                lines = content.split('\n')
                new_lines = []
                replaced = False
                for i, line in enumerate(lines):
                    if 'const API_BASE =' in line and not replaced:
                        new_lines.append("// Auto-detect API base URL based on current page")
                        new_lines.append("const API_BASE = (() => {")
                        new_lines.append("    if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {")
                        new_lines.append("        return '';")
                        new_lines.append("    }")
                        new_lines.append("    return 'http://127.0.0.1:5050';")
                        new_lines.append("})();")
                        replaced = True
                    else:
                        new_lines.append(line)
                content = '\n'.join(new_lines)
                print("✓ Replaced API_BASE definition")
    
    # Also fix the apiCall function URL construction
    if 'const url = `${API_BASE}${endpoint}`;' in content:
        # Already correct
        pass
    elif '`${API_BASE}${endpoint}`' in content:
        # Update the line to handle empty API_BASE
        content = content.replace(
            'const url = `${API_BASE}${endpoint}`;',
            '// Use relative path if API_BASE is empty (same origin), otherwise use full URL\n        const url = API_BASE ? `${API_BASE}${endpoint}` : endpoint;'
        )
        print("✓ Updated URL construction")
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Successfully updated {file_path}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
PYTHON_SCRIPT

echo ""
echo "Verifying fix..."
docker exec smartcursor head -20 /app/static/js/auth.js

echo ""
echo "✅ Done! File has been fixed."
echo "Please refresh your browser (Ctrl+F5) and test login."


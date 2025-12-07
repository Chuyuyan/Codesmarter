#!/bin/bash
# Create fix script and run it in container

cat > /tmp/fix_auth_container.py << 'SCRIPT'
import sys

file_path = '/app/static/js/auth.js'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"File size: {len(content)} characters")
    print("Searching for API_BASE line...\n")
    
    # Find and replace
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
        print("✓ Found and replaced API_BASE definition")
    else:
        # Try line-by-line approach
        lines = content.split('\n')
        found = False
        for i, line in enumerate(lines):
            if 'const API_BASE' in line and '127.0.0.1' in line:
                lines[i] = "// Auto-detect API base URL based on current page"
                lines.insert(i+1, "const API_BASE = (() => {")
                lines.insert(i+2, "    if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {")
                lines.insert(i+3, "        return '';")
                lines.insert(i+4, "    }")
                lines.insert(i+5, "    return 'http://127.0.0.1:5050';")
                lines.insert(i+6, "})();")
                content = '\n'.join(lines)
                print(f"✓ Found and replaced at line {i+1}")
                found = True
                break
        
        if not found:
            print("✗ Could not find API_BASE line")
            sys.exit(1)
    
    # Fix URL construction
    if 'const url = `${API_BASE}${endpoint}`;' in content and 'Use relative path' not in content:
        content = content.replace(
            '        const url = `${API_BASE}${endpoint}`;',
            '        // Use relative path if API_BASE is empty\n        const url = API_BASE ? `${API_BASE}${endpoint}` : endpoint;'
        )
        print("✓ Updated URL construction")
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✓ File saved successfully!")
    print("\nFirst 20 lines:")
    print('\n'.join(content.split('\n')[:20]))
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
SCRIPT

# Copy script to container
docker cp /tmp/fix_auth_container.py smartcursor:/tmp/fix_auth_container.py

# Run it
docker exec smartcursor python3 /tmp/fix_auth_container.py


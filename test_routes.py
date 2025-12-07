"""Quick script to test if routes are registered"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from backend.app import app, STATIC_DIR
    
    print("\n" + "="*70)
    print("ROUTE DIAGNOSTIC TEST")
    print("="*70)
    
    print(f"\nSTATIC_DIR: {STATIC_DIR}")
    print(f"STATIC_DIR exists: {STATIC_DIR.exists()}")
    
    if STATIC_DIR.exists():
        html_files = list(STATIC_DIR.glob('*.html'))
        print(f"HTML files: {[f.name for f in html_files]}")
        print(f"dashboard.html exists: {(STATIC_DIR / 'dashboard.html').exists()}")
    
    print(f"\nRegistered routes:")
    print("-"*70)
    routes = []
    for rule in app.url_map.iter_rules():
        methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        routes.append((rule.rule, methods))
    
    routes.sort(key=lambda x: x[0])
    for route, methods in routes:
        marker = " <-- DASHBOARD!" if '/dashboard' in route else ""
        print(f"  {route:50s} [{methods}]{marker}")
    
    print("\n" + "="*70)
    
    # Check if dashboard route exists
    dashboard_routes = [r for r in routes if '/dashboard' in r[0]]
    if dashboard_routes:
        print(f"\n✅ Dashboard route IS registered: {dashboard_routes}")
    else:
        print(f"\n❌ Dashboard route NOT found in registered routes!")
    
    print("="*70 + "\n")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()


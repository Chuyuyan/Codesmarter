"""Entry point for running the Flask app as a module"""
from backend.app import app
from backend.app import STATIC_DIR
from pathlib import Path

if __name__ == "__main__":
    # Print all registered routes for debugging
    print("\n" + "="*70)
    print("REGISTERED ROUTES:")
    print("="*70)
    routes = []
    for rule in app.url_map.iter_rules():
        methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        routes.append((rule.rule, methods))
    
    # Sort routes for better readability
    routes.sort(key=lambda x: x[0])
    for route, methods in routes:
        print(f"  {route:50s} [{methods}]")
    
    print("="*70)
    print(f"\nSTATIC_DIR: {STATIC_DIR}")
    print(f"STATIC_DIR exists: {STATIC_DIR.exists()}")
    if STATIC_DIR.exists():
        html_files = list(STATIC_DIR.glob('*.html'))
        print(f"HTML files in static: {[f.name for f in html_files]}")
        print(f"dashboard.html exists: {(STATIC_DIR / 'dashboard.html').exists()}")
    else:
        print(f"[ERROR] STATIC_DIR does not exist!")
    print("="*70 + "\n")
    
    app.run(host="0.0.0.0", port=5050, debug=True)


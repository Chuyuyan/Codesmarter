"""Check database columns"""
import sqlite3
from pathlib import Path

db_path = Path("data/users.db").resolve()
print(f"Checking database: {db_path}")
print(f"Exists: {db_path.exists()}")

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print("\nColumns in users table:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    col_names = [col[1] for col in columns]
    print(f"\nHas phone_number: {'phone_number' in col_names}")
    
    if 'phone_number' not in col_names:
        print("\nAdding phone_number column...")
        cursor.execute("ALTER TABLE users ADD COLUMN phone_number VARCHAR(20)")
        conn.commit()
        print("Done!")
    else:
        print("\nphone_number column already exists")
    
    conn.close()
else:
    print("Database not found!")


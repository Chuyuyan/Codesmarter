"""
Standalone database migration script.
Run this to add the phone_number column to the users table.

Usage:
    python migrate_database.py
"""
from pathlib import Path
import sys
import sqlite3
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.modules.database import db
from flask import Flask

def migrate_database():
    """Add phone_number column to users table if it doesn't exist."""
    # Create Flask app for app context
    app = Flask(__name__)
    
    # Initialize database
    from backend.modules.database import init_database
    init_database(app)
    
    with app.app_context():
        # Get database path
        db_path = os.getenv("DATABASE_PATH", "data/users.db")
        if not os.path.isabs(db_path):
            db_path = str(project_root / db_path)
        
        db_path_normalized = str(Path(db_path).resolve())
        
        if not os.path.exists(db_path_normalized):
            print(f"[ERROR] Database file not found at: {db_path_normalized}")
            print("   Database will be created with new schema when server starts.")
            return
        
        print(f"[INFO] Database file: {db_path_normalized}")
        
        # Connect directly to SQLite
        conn = sqlite3.connect(db_path_normalized)
        cursor = conn.cursor()
        
        try:
            # Check if users table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if not cursor.fetchone():
                print("[WARNING] Users table doesn't exist yet.")
                print("   Tables will be created with new schema when server starts.")
                conn.close()
                return
            
            # Check if phone_number column exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'phone_number' in columns:
                print("[SUCCESS] phone_number column already exists in users table")
                conn.close()
                return
            
            # Add phone_number column
            print("[INFO] Adding phone_number column to users table...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN phone_number VARCHAR(20) NULL
            """)
            
            # Create index
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_phone_number ON users(phone_number)")
                print("[SUCCESS] Created index on phone_number column")
            except Exception as e:
                print(f"[WARNING] Could not create index: {e}")
            
            conn.commit()
            print("[SUCCESS] Successfully added phone_number column!")
            
        except Exception as e:
            print(f"[ERROR] Error during migration: {e}")
            conn.rollback()
            import traceback
            traceback.print_exc()
        finally:
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Adding phone_number column")
    print("=" * 60)
    migrate_database()
    print("=" * 60)
    print("Migration complete!")
    print("=" * 60)

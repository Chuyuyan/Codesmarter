"""
Database migration to add phone_number column to users table.
This migration is safe to run multiple times.
"""
from backend.modules.database import db
import sqlite3
from pathlib import Path
import os


def migrate_phone_number_column():
    """
    Add phone_number column to users table if it doesn't exist.
    Safe to run multiple times - checks if column exists first.
    """
    try:
        # Get database path
        db_path = os.getenv("DATABASE_PATH", "data/users.db")
        if not os.path.isabs(db_path):
            project_root = Path(__file__).parent.parent.parent
            db_path = str(project_root / db_path)
        
        db_path_normalized = str(Path(db_path).resolve())
        
        # Check if database file exists
        if not os.path.exists(db_path_normalized):
            print("[migration] Database file doesn't exist yet. Tables will be created with new schema.")
            return
        
        # Connect directly to SQLite to check column existence
        conn = sqlite3.connect(db_path_normalized)
        cursor = conn.cursor()
        
        # Check if phone_number column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'phone_number' in columns:
            print("[migration] phone_number column already exists in users table")
            conn.close()
            return
        
        # Add phone_number column
        print("[migration] Adding phone_number column to users table...")
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN phone_number VARCHAR(20) NULL
        """)
        
        # Create index for phone_number
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_phone_number ON users(phone_number)")
        except Exception as e:
            print(f"[migration] Note: Could not create index (may already exist): {e}")
        
        conn.commit()
        conn.close()
        
        print("[migration] Successfully added phone_number column to users table")
        
    except Exception as e:
        print(f"[migration] Error during migration: {e}")
        # Don't raise - allow server to continue
        import traceback
        traceback.print_exc()

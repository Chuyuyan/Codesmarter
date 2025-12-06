"""
Database migration utilities for schema updates.
"""
import sqlite3
import os
from pathlib import Path
from backend.modules.database import db


def add_phone_number_column():
    """
    Add phone_number column to users table if it doesn't exist.
    Safe to run multiple times.
    """
    db_path = os.getenv("DATABASE_PATH", "data/users.db")
    db_path = Path(db_path).resolve()
    
    if not db_path.exists():
        print(f"[migration] Database file not found at {db_path}, will be created on next init")
        return
    
    try:
        # Connect directly to SQLite database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if phone_number column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'phone_number' in columns:
            print("[migration] phone_number column already exists")
            conn.close()
            return
        
        # Add phone_number column
        print("[migration] Adding phone_number column to users table...")
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN phone_number VARCHAR(20)
        """)
        
        # Create index on phone_number
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS ix_users_phone_number 
                ON users(phone_number)
            """)
        except sqlite3.OperationalError as e:
            # Index might already exist or creation failed
            print(f"[migration] Index creation note: {e}")
        
        conn.commit()
        conn.close()
        
        print("[migration] ✅ phone_number column added successfully!")
        
    except Exception as e:
        print(f"[migration] ❌ Error adding phone_number column: {e}")
        raise


def run_migrations():
    """Run all pending migrations."""
    print("[migration] Running database migrations...")
    try:
        add_phone_number_column()
        print("[migration] ✅ All migrations completed!")
    except Exception as e:
        print(f"[migration] ❌ Migration failed: {e}")
        raise


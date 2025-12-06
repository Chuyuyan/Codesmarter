"""
Database initialization and configuration.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
import os

# Initialize SQLAlchemy
db = SQLAlchemy()

def init_database(app: Flask):
    """
    Initialize database for Flask app.
    
    Args:
        app: Flask application instance
    """
    # Database configuration
    db_path = os.getenv("DATABASE_PATH", "data/users.db")
    
    # Convert to absolute path to avoid issues
    if not os.path.isabs(db_path):
        # Get project root (parent of backend directory)
        project_root = Path(__file__).parent.parent.parent
        db_path = str(project_root / db_path)
    
    # Ensure directory exists
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Use absolute path for SQLite URI
    # SQLite requires forward slashes or raw string on Windows
    db_path_normalized = str(Path(db_path).resolve()).replace('\\', '/')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path_normalized}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize db with app
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        from backend.modules.user_auth import UserAuth
        user_auth = UserAuth(db)
        user_auth.create_tables()
        
        # Run migrations (add new columns if needed)
        try:
            from backend.modules.migrate_phone_number import migrate_phone_number_column
            migrate_phone_number_column()
        except ImportError:
            # Migration module doesn't exist yet - that's okay
            pass
        except Exception as e:
            print(f"[database] Migration warning: {e}")
        
        print(f"[database] Database initialized at {db_path_normalized}")
    
    return db


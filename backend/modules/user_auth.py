"""
User authentication and management module.
Handles user registration, login, logout, and session management.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import secrets
import jwt
import os
from functools import wraps

from flask import request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

# Import database
from backend.modules.database import db

# JWT secret key (should be in config/env in production)
# Use environment variable if set, otherwise generate a fixed key for development
# IMPORTANT: In production, set JWT_SECRET_KEY in environment variables!
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production-12345")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days


# User model
class User(db.Model):
    """User model for authentication."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True, index=True)  # E.164 format: +1234567890
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationship to repositories
    repositories = db.relationship('UserRepository', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary."""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone_number': self.phone_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'is_admin': self.is_admin
        }
        if include_sensitive:
            data['password_hash'] = self.password_hash
        return data


# UserRepository model - links users to their repositories
class UserRepository(db.Model):
    """Model to track which repositories belong to which users."""
    __tablename__ = 'user_repositories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    repo_id = db.Column(db.String(255), nullable=False, index=True)  # Repository identifier
    repo_path = db.Column(db.String(512), nullable=False)  # Full path to repository
    repo_name = db.Column(db.String(255), nullable=False)  # Display name
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_indexed = db.Column(db.Boolean, default=False)  # Whether repo is indexed
    chunks_count = db.Column(db.Integer, default=0)  # Number of indexed chunks
    
    # Unique constraint: one user can't have the same repo_id twice
    __table_args__ = (db.UniqueConstraint('user_id', 'repo_id', name='uq_user_repo'),)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'repo_id': self.repo_id,
            'repo_path': self.repo_path,
            'repo_name': self.repo_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_indexed': self.is_indexed,
            'chunks_count': self.chunks_count
        }


# PasswordResetToken model
class PasswordResetToken(db.Model):
    """Model for password reset tokens."""
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    used = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to user
    user = db.relationship('User', backref='reset_tokens')
    
    def is_valid(self):
        """Check if token is valid (not expired and not used)."""
        return not self.used and datetime.utcnow() < self.expires_at
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used': self.used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserAuth:
    """User authentication and management."""
    
    def __init__(self, db_instance):
        """
        Initialize with database connection.
        
        Args:
            db_instance: SQLAlchemy database instance
        """
        self.db = db_instance
        self.User = User
        self.UserRepository = UserRepository
        self.PasswordResetToken = PasswordResetToken
    
    def create_tables(self):
        """Create database tables."""
        db.create_all()
    
    # Repository management methods
    def add_user_repository(self, user_id: int, repo_id: str, repo_path: str, repo_name: str = None) -> Dict:
        """
        Add a repository to a user's account.
        
        Args:
            user_id: User ID
            repo_id: Repository identifier
            repo_path: Full path to repository
            repo_name: Display name (defaults to repo_id)
        
        Returns:
            Dictionary with success status and repository data
        """
        if repo_name is None:
            repo_name = repo_id
        
        # Check if repository already exists for this user
        existing = self.UserRepository.query.filter_by(
            user_id=user_id,
            repo_id=repo_id
        ).first()
        
        if existing:
            # Update existing
            existing.repo_path = repo_path
            existing.repo_name = repo_name
            existing.updated_at = datetime.utcnow()
            db.session.commit()
            return {
                "ok": True,
                "repository": existing.to_dict(),
                "message": "Repository updated"
            }
        
        # Create new
        try:
            new_repo = self.UserRepository(
                user_id=user_id,
                repo_id=repo_id,
                repo_path=repo_path,
                repo_name=repo_name
            )
            db.session.add(new_repo)
            db.session.commit()
            return {
                "ok": True,
                "repository": new_repo.to_dict(),
                "message": "Repository added"
            }
        except Exception as e:
            db.session.rollback()
            return {"ok": False, "error": f"Failed to add repository: {str(e)}"}
    
    def get_user_repositories(self, user_id: int) -> List[object]:
        """Get all repositories for a user."""
        return self.UserRepository.query.filter_by(user_id=user_id).all()
    
    def get_user_repository(self, user_id: int, repo_id: str) -> Optional[object]:
        """Get a specific repository for a user."""
        return self.UserRepository.query.filter_by(
            user_id=user_id,
            repo_id=repo_id
        ).first()
    
    def update_repository_index_status(self, user_id: int, repo_id: str, is_indexed: bool, chunks_count: int = 0) -> Dict:
        """Update repository indexing status."""
        repo = self.get_user_repository(user_id, repo_id)
        if not repo:
            return {"ok": False, "error": "Repository not found"}
        
        try:
            repo.is_indexed = is_indexed
            repo.chunks_count = chunks_count
            repo.updated_at = datetime.utcnow()
            db.session.commit()
            return {"ok": True, "repository": repo.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {"ok": False, "error": f"Failed to update: {str(e)}"}
    
    def delete_user_repository(self, user_id: int, repo_id: str) -> Dict:
        """Delete a repository from user's account."""
        repo = self.get_user_repository(user_id, repo_id)
        if not repo:
            return {"ok": False, "error": "Repository not found"}
        
        try:
            db.session.delete(repo)
            db.session.commit()
            return {"ok": True, "message": "Repository deleted"}
        except Exception as e:
            db.session.rollback()
            return {"ok": False, "error": f"Failed to delete: {str(e)}"}
    
    def register_user(self, username: str, email: str, password: str) -> Dict:
        """
        Register a new user.
        
        Args:
            username: Unique username
            email: Unique email address
            password: Plain text password (will be hashed)
        
        Returns:
            Dictionary with success status and user data or error
        """
        # Validate input
        if not username or len(username) < 3:
            return {"ok": False, "error": "Username must be at least 3 characters"}
        
        if not email or "@" not in email:
            return {"ok": False, "error": "Invalid email address"}
        
        if not password or len(password) < 6:
            return {"ok": False, "error": "Password must be at least 6 characters"}
        
        # Check if user already exists
        existing_user = self.User.query.filter(
            (self.User.username == username) | (self.User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                return {"ok": False, "error": "Username already taken"}
            else:
                return {"ok": False, "error": "Email already registered"}
        
        # Create new user
        try:
            new_user = self.User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                is_active=True
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            return {
                "ok": True,
                "user": new_user.to_dict(),
                "message": "User registered successfully"
            }
        except Exception as e:
            db.session.rollback()
            return {"ok": False, "error": f"Registration failed: {str(e)}"}
    
    def login_user(self, username_or_email: str, password: str) -> Dict:
        """
        Authenticate user and create session.
        
        Args:
            username_or_email: Username or email address
            password: Plain text password
        
        Returns:
            Dictionary with success status, JWT token, and user data or error
        """
        # Find user by username or email
        user = self.User.query.filter(
            (self.User.username == username_or_email) | (self.User.email == username_or_email)
        ).first()
        
        if not user:
            return {"ok": False, "error": "Invalid username/email or password"}
        
        if not user.is_active:
            return {"ok": False, "error": "Account is disabled"}
        
        # Check password
        if not check_password_hash(user.password_hash, password):
            return {"ok": False, "error": "Invalid username/email or password"}
        
        # Generate JWT token
        token = self._generate_token(user.id, user.username)
        
        return {
            "ok": True,
            "token": token,
            "user": user.to_dict(),
            "message": "Login successful"
        }
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify JWT token and return user info.
        
        Args:
            token: JWT token string
        
        Returns:
            Dictionary with user_id and username, or None if invalid
        """
        try:
            print(f"[verify_token] Attempting to verify token (first 20 chars): {token[:20] if token else 'EMPTY'}...")
            print(f"[verify_token] Using JWT_SECRET_KEY (first 10 chars): {JWT_SECRET_KEY[:10]}...")
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            print(f"[verify_token] ✅ Token verified successfully! User ID: {payload.get('user_id')}, Username: {payload.get('username')}")
            return {
                "user_id": payload.get("user_id"),
                "username": payload.get("username")
            }
        except jwt.ExpiredSignatureError as e:
            print(f"[verify_token] ❌ Token expired: {e}")
            return None
        except jwt.InvalidTokenError as e:
            print(f"[verify_token] ❌ Invalid token: {e}")
            return None
        except Exception as e:
            print(f"[verify_token] ❌ Unexpected error: {e}")
            import traceback
            print(f"[verify_token] Traceback:\n{traceback.format_exc()}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[object]:
        """Get user by ID."""
        return self.User.query.filter(self.User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[object]:
        """Get user by username."""
        return self.User.query.filter(self.User.username == username).first()
    
    def update_user(self, user_id: int, **kwargs) -> Dict:
        """
        Update user information.
        
        Args:
            user_id: User ID
            **kwargs: Fields to update (email, password, etc.)
        
        Returns:
            Dictionary with success status and updated user data
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return {"ok": False, "error": "User not found"}
        
        try:
            if "email" in kwargs:
                # Check if email is already taken
                existing = self.User.query.filter(
                    self.User.email == kwargs["email"],
                    self.User.id != user_id
                ).first()
                if existing:
                    return {"ok": False, "error": "Email already taken"}
                user.email = kwargs["email"]
            
            if "password" in kwargs:
                user.password_hash = generate_password_hash(kwargs["password"])
            
            if "username" in kwargs:
                # Check if username is already taken
                existing = self.User.query.filter(
                    self.User.username == kwargs["username"],
                    self.User.id != user_id
                ).first()
                if existing:
                    return {"ok": False, "error": "Username already taken"}
                user.username = kwargs["username"]
            
            if "phone_number" in kwargs:
                # Allow setting or clearing phone number
                phone = kwargs["phone_number"]
                if phone is None or phone == "":
                    user.phone_number = None
                else:
                    # Validate E.164 format (basic check)
                    if not phone.startswith("+") or len(phone) < 8:
                        return {"ok": False, "error": "Phone number must be in E.164 format (e.g., +1234567890)"}
                    user.phone_number = phone
            
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                "ok": True,
                "user": user.to_dict(),
                "message": "User updated successfully"
            }
        except Exception as e:
            db.session.rollback()
            return {"ok": False, "error": f"Update failed: {str(e)}"}
    
    def delete_user(self, user_id: int) -> Dict:
        """
        Delete user account.
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with success status
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return {"ok": False, "error": "User not found"}
        
        try:
            db.session.delete(user)
            db.session.commit()
            return {"ok": True, "message": "User deleted successfully"}
        except Exception as e:
            db.session.rollback()
            return {"ok": False, "error": f"Delete failed: {str(e)}"}
    
    def _generate_token(self, user_id: int, username: str) -> str:
        """Generate JWT token for user."""
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        print(f"[_generate_token] Generated token for user {username} (ID: {user_id}) using secret key (first 10 chars): {JWT_SECRET_KEY[:10]}...")
        return token
    
    def request_password_reset(self, email: str, base_url: str = None) -> Dict:
        """
        Request a password reset for a user.
        
        Args:
            email: User's email address
        
        Returns:
            Dictionary with success status and reset token (for development)
        """
        # Find user by email
        user = self.User.query.filter(self.User.email == email).first()
        
        if not user:
            # Don't reveal if email exists (security best practice)
            return {
                "ok": True,
                "message": "If an account with that email exists, a password reset link has been sent."
            }
        
        # Invalidate any existing unused tokens for this user
        existing_tokens = self.PasswordResetToken.query.filter_by(
            user_id=user.id,
            used=False
        ).all()
        
        for token in existing_tokens:
            token.used = True
        
        # Generate new reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        
        try:
            reset_token_obj = self.PasswordResetToken(
                user_id=user.id,
                token=reset_token,
                expires_at=expires_at,
                used=False
            )
            db.session.add(reset_token_obj)
            db.session.commit()
            
            # Generate reset URL
            base_url = base_url or os.getenv('BASE_URL', 'http://localhost:5050')
            reset_url = f"{base_url}/reset-password?token={reset_token}"
            
            email_sent = False
            sms_sent = False
            
            # Try to send email
            try:
                from backend.modules.email_sender import get_email_sender
                email_sender = get_email_sender()
                email_sender.base_url = base_url
                
                email_result = email_sender.send_password_reset_email(
                    to_email=email,
                    reset_token=reset_token,
                    username=user.username
                )
                
                if email_result.get("ok"):
                    email_sent = True
                    print(f"[password_reset] Password reset email sent to {email}")
                else:
                    print(f"[password_reset] Email sending failed: {email_result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"[password_reset] Email sending exception: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # Try to send SMS if user has phone number
            if user.phone_number:
                try:
                    from backend.modules.sms_sender import get_sms_sender
                    sms_sender = get_sms_sender()
                    sms_sender.base_url = base_url
                    
                    sms_result = sms_sender.send_password_reset_sms(
                        to_number=user.phone_number,
                        reset_token=reset_token,
                        username=user.username
                    )
                    
                    if sms_result.get("ok"):
                        sms_sent = True
                        print(f"[password_reset] Password reset SMS sent to {user.phone_number}")
                except Exception as e:
                    print(f"[password_reset] SMS sending failed: {str(e)}")
            
            # If either email or SMS was sent, return success
            if email_sent or sms_sent:
                return {
                    "ok": True,
                    "message": "If an account with that email exists, a password reset link has been sent.",
                    "email_sent": email_sent,
                    "sms_sent": sms_sent
                }
            
            # Neither email nor SMS sent - show token for development
            print(f"[password_reset] Reset token for {email}: {reset_token}")
            print(f"[password_reset] Reset URL: {reset_url}")
            
            return {
                "ok": True,
                "message": "If an account with that email exists, a password reset link has been sent.",
                "token": reset_token,  # Development mode - shown when notifications not configured
                "reset_url": reset_url,
                "email_sent": False,
                "sms_sent": False,
                "note": "Email/SMS sending not configured. Token shown for development/testing."
            }
        except Exception as e:
            db.session.rollback()
            return {"ok": False, "error": f"Failed to create reset token: {str(e)}"}
    
    def verify_reset_token(self, token: str) -> Dict:
        """
        Verify a password reset token.
        
        Args:
            token: Reset token string
        
        Returns:
            Dictionary with success status and user info if valid
        """
        reset_token = self.PasswordResetToken.query.filter_by(token=token).first()
        
        if not reset_token:
            return {"ok": False, "error": "Invalid reset token"}
        
        if not reset_token.is_valid():
            if reset_token.used:
                return {"ok": False, "error": "Reset token has already been used"}
            else:
                return {"ok": False, "error": "Reset token has expired"}
        
        user = self.get_user_by_id(reset_token.user_id)
        if not user:
            return {"ok": False, "error": "User not found"}
        
        return {
            "ok": True,
            "user": user.to_dict(),
            "token_id": reset_token.id
        }
    
    def reset_password(self, token: str, new_password: str) -> Dict:
        """
        Reset user's password using a reset token.
        
        Args:
            token: Reset token string
            new_password: New password (plain text)
        
        Returns:
            Dictionary with success status
        """
        # Validate password
        if not new_password or len(new_password) < 6:
            return {"ok": False, "error": "Password must be at least 6 characters"}
        
        # Verify token
        reset_token = self.PasswordResetToken.query.filter_by(token=token).first()
        
        if not reset_token:
            return {"ok": False, "error": "Invalid reset token"}
        
        if not reset_token.is_valid():
            if reset_token.used:
                return {"ok": False, "error": "Reset token has already been used"}
            else:
                return {"ok": False, "error": "Reset token has expired"}
        
        # Get user
        user = self.get_user_by_id(reset_token.user_id)
        if not user:
            return {"ok": False, "error": "User not found"}
        
        try:
            # Update password
            user.password_hash = generate_password_hash(new_password)
            user.updated_at = datetime.utcnow()
            
            # Mark token as used
            reset_token.used = True
            
            db.session.commit()
            
            return {
                "ok": True,
                "message": "Password reset successfully"
            }
        except Exception as e:
            db.session.rollback()
            return {"ok": False, "error": f"Failed to reset password: {str(e)}"}


def require_auth(f):
    """
    Decorator to require authentication for an endpoint.
    
    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            user_id = request.current_user_id
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"[require_auth] Checking authentication for {f.__name__}")
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        print(f"[require_auth] Authorization header: {auth_header[:50] if auth_header else 'NOT FOUND'}...")
        
        if not auth_header:
            print("[require_auth] ❌ No Authorization header")
            return jsonify({"ok": False, "error": "Authorization header missing"}), 401
        
        # Extract token (format: "Bearer <token>")
        try:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            print(f"[require_auth] Token extracted (first 20 chars): {token[:20] if token else 'EMPTY'}...")
        except IndexError:
            print("[require_auth] ❌ Invalid authorization format")
            return jsonify({"ok": False, "error": "Invalid authorization format"}), 401
        
        # Verify token using UserAuth instance from app context
        if not hasattr(g, 'user_auth'):
            print("[require_auth] ❌ user_auth not in g context")
            return jsonify({"ok": False, "error": "Authentication not configured"}), 500
        
        user_info = g.user_auth.verify_token(token)
        print(f"[require_auth] Token verification result: {user_info}")
        
        if not user_info:
            print("[require_auth] ❌ Token invalid or expired")
            return jsonify({"ok": False, "error": "Invalid or expired token"}), 401
        
        # Attach user info to request
        request.current_user_id = user_info["user_id"]
        request.current_username = user_info["username"]
        print(f"[require_auth] ✅ Authenticated user: {user_info['username']} (ID: {user_info['user_id']})")
        
        return f(*args, **kwargs)
    
    return decorated_function


"""
Helper functions for user-specific repository operations.
Ensures users can only access their own repositories.
"""
from typing import List, Optional
from pathlib import Path
from backend.modules.user_auth import UserAuth
from backend.modules.multi_repo import repo_id_from_path


def get_user_repo_dirs(user_auth: UserAuth, user_id: int) -> List[str]:
    """
    Get list of repository directories for a user.
    
    Args:
        user_auth: UserAuth instance
        user_id: User ID
    
    Returns:
        List of repository directory paths
    """
    user_repos = user_auth.get_user_repositories(user_id)
    return [repo.repo_path for repo in user_repos if repo.is_indexed]


def verify_user_owns_repo(user_auth: UserAuth, user_id: int, repo_dir: str) -> bool:
    """
    Verify that a repository belongs to a user.
    
    Args:
        user_auth: UserAuth instance
        user_id: User ID
        repo_dir: Repository directory path
    
    Returns:
        True if user owns the repo, False otherwise
    """
    repo_id = repo_id_from_path(repo_dir)
    repo = user_auth.get_user_repository(user_id, repo_id)
    return repo is not None


def get_user_repo_ids(user_auth: UserAuth, user_id: int) -> List[str]:
    """
    Get list of repository IDs for a user.
    
    Args:
        user_auth: UserAuth instance
        user_id: User ID
    
    Returns:
        List of repository IDs
    """
    user_repos = user_auth.get_user_repositories(user_id)
    return [repo.repo_id for repo in user_repos if repo.is_indexed]


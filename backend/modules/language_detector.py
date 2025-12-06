"""
Detect programming languages from existing code in a directory.
Used to determine preferred languages when generating new code.
"""
from pathlib import Path
from typing import Dict, Optional, Set
import os


# File extension to language mapping
EXTENSION_TO_LANGUAGE = {
    # Frontend languages
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.vue': 'vue',
    '.html': 'html',
    '.css': 'css',
    
    # Backend languages
    '.py': 'python',
    '.java': 'java',
    '.go': 'go',
    '.rs': 'rust',
    '.cpp': 'cpp',
    '.c': 'c',
    '.cs': 'csharp',
    '.php': 'php',
    '.rb': 'ruby',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    
    # Database/Config
    '.sql': 'sql',
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.xml': 'xml',
    '.toml': 'toml',
}


# Framework indicators
FRAMEWORK_INDICATORS = {
    'react': ['package.json', 'react', 'react-dom'],
    'vue': ['vue.config.js', 'nuxt.config.js'],
    'angular': ['angular.json', '@angular/core'],
    'nextjs': ['next.config.js'],
    'express': ['express', 'package.json'],
    'flask': ['flask', 'requirements.txt', 'app.py'],
    'django': ['django', 'manage.py', 'settings.py'],
    'fastapi': ['fastapi', 'uvicorn'],
    'spring': ['pom.xml', 'build.gradle', 'Application.java'],
    'rails': ['Gemfile', 'config.ru', 'application.rb'],
}


def detect_languages_from_directory(directory: str) -> Dict[str, Set[str]]:
    """
    Detect programming languages used in a directory.
    
    Returns:
        Dictionary with 'frontend', 'backend', 'other' sets of languages
    """
    detected = {
        'frontend': set(),
        'backend': set(),
        'other': set()
    }
    
    if not directory or not os.path.exists(directory):
        return detected
    
    dir_path = Path(directory)
    
    # Check for framework indicators first
    for framework, indicators in FRAMEWORK_INDICATORS.items():
        for indicator in indicators:
            if (dir_path / indicator).exists() or \
               any((dir_path.rglob(indicator))):
                if framework in ['react', 'vue', 'angular', 'nextjs']:
                    detected['frontend'].add(framework)
                elif framework in ['express', 'flask', 'django', 'fastapi', 'spring', 'rails']:
                    detected['backend'].add(framework)
    
    # Scan files for extensions
    frontend_extensions = {'.js', '.jsx', '.ts', '.tsx', '.vue', '.html', '.css'}
    backend_extensions = {'.py', '.java', '.go', '.rs', '.php', '.rb', '.cpp', '.c'}
    
    for ext in frontend_extensions:
        if any(dir_path.rglob(f'*{ext}')):
            lang = EXTENSION_TO_LANGUAGE.get(ext)
            if lang:
                detected['frontend'].add(lang)
    
    for ext in backend_extensions:
        if any(dir_path.rglob(f'*{ext}')):
            lang = EXTENSION_TO_LANGUAGE.get(ext)
            if lang:
                detected['backend'].add(lang)
    
    return detected


def detect_stack_from_directory(directory: str) -> Dict[str, str]:
    """
    Detect tech stack (frontend framework, backend framework, database) from directory.
    
    Returns:
        Dictionary with 'frontend', 'backend', 'database' keys
    """
    languages = detect_languages_from_directory(directory)
    stack = {
        'frontend': None,
        'backend': None,
        'database': None
    }
    
    # Determine frontend framework
    if 'react' in languages['frontend'] or 'javascript' in languages['frontend']:
        stack['frontend'] = 'react'
    elif 'vue' in languages['frontend']:
        stack['frontend'] = 'vue'
    elif 'angular' in languages['frontend']:
        stack['frontend'] = 'angular'
    elif 'typescript' in languages['frontend']:
        stack['frontend'] = 'react'  # Default for TypeScript
    
    # Determine backend framework
    if 'flask' in languages['backend'] or 'python' in languages['backend']:
        stack['backend'] = 'flask'
    elif 'django' in languages['backend']:
        stack['backend'] = 'django'
    elif 'fastapi' in languages['backend']:
        stack['backend'] = 'fastapi'
    elif 'express' in languages['backend']:
        stack['backend'] = 'express'
    elif 'spring' in languages['backend'] or 'java' in languages['backend']:
        stack['backend'] = 'spring'
    elif 'go' in languages['backend']:
        stack['backend'] = 'go'
    elif 'rust' in languages['backend']:
        stack['backend'] = 'rust'
    
    # Check for database files
    db_path = Path(directory)
    if (db_path / 'schema.sql').exists() or any(db_path.rglob('*.sqlite')):
        stack['database'] = 'sqlite'
    elif any(db_path.rglob('*.pg')):
        stack['database'] = 'postgresql'
    elif (db_path / 'package.json').exists():
        # Check package.json for database drivers
        try:
            import json
            pkg_json = db_path / 'package.json'
            if pkg_json.exists():
                with open(pkg_json, 'r') as f:
                    pkg = json.load(f)
                    deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                    if 'pg' in deps or 'postgres' in deps:
                        stack['database'] = 'postgresql'
                    elif 'mysql' in deps or 'mysql2' in deps:
                        stack['database'] = 'mysql'
                    elif 'mongodb' in deps or 'mongoose' in deps:
                        stack['database'] = 'mongodb'
        except:
            pass
    
    return stack

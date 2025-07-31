"""Analysis workflow and business logic constants."""

from typing import  Set

class RepositoryConstants:
    """Constants related to analysis workflow and business rules."""
    
    # Project Detection
    IGNORED_DIRECTORIES: Set[str] = {
        ".git", ".svn", ".hg",
        "node_modules", "__pycache__", ".pytest_cache",
        "target", "build", "dist", "out",
        ".vscode", ".idea", ".vs",
        "vendor", "deps", ".deps"
    }
    
"""Repository scanning functionality."""

from collections.abc import Generator
from pathlib import Path

from gittyup import constants


def is_git_repo(path: Path) -> bool:
    """
    Check if a directory is a Git repository.

    Args:
        path: Directory path to check

    Returns:
        True if the directory contains a .git folder
    """
    git_dir = path / constants.GIT_DIR
    return git_dir.exists() and git_dir.is_dir()


def should_exclude(path: Path, exclude_patterns: list[str]) -> bool:
    """
    Check if a path should be excluded based on patterns.

    Args:
        path: Path to check
        exclude_patterns: List of directory names to exclude

    Returns:
        True if the path should be excluded
    """
    return path.name in exclude_patterns


def scan_directory(
    root_path: Path,
    max_depth: int | None = None,
    exclude_patterns: list[str] | None = None,
    current_depth: int = 0,
) -> Generator[Path, None, None]:
    """
    Recursively scan a directory tree to find Git repositories.

    Args:
        root_path: Root directory to start scanning
        max_depth: Maximum depth to traverse (None for unlimited)
        exclude_patterns: List of directory names to exclude
        current_depth: Current recursion depth (internal use)

    Yields:
        Path objects for each Git repository found
    """
    if exclude_patterns is None:
        exclude_patterns = constants.DEFAULT_EXCLUDES

    # Check if we've reached max depth
    if max_depth is not None and current_depth > max_depth:
        return

    # Check if this directory itself is a git repo
    if is_git_repo(root_path):
        yield root_path
        # Don't descend into subdirectories of a git repo
        return

    # Scan subdirectories
    try:
        for item in sorted(root_path.iterdir()):
            # Skip files and excluded directories
            if not item.is_dir():
                continue

            if should_exclude(item, exclude_patterns):
                continue

            # Recursively scan subdirectory
            yield from scan_directory(
                item,
                max_depth=max_depth,
                exclude_patterns=exclude_patterns,
                current_depth=current_depth + 1,
            )
    except PermissionError:
        # Skip directories we can't access
        pass

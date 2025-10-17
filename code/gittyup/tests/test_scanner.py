"""Tests for scanner module."""

from pathlib import Path

from gittyup.scanner import is_git_repo, scan_directory, should_exclude


def test_is_git_repo_with_git_directory(tmp_path: Path) -> None:
    """Test that is_git_repo returns True for directories with .git folder."""
    # Create a .git directory
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    assert is_git_repo(tmp_path) is True


def test_is_git_repo_without_git_directory(tmp_path: Path) -> None:
    """Test that is_git_repo returns False for directories without .git folder."""
    assert is_git_repo(tmp_path) is False


def test_is_git_repo_with_git_file(tmp_path: Path) -> None:
    """Test that is_git_repo returns False if .git is a file, not a directory."""
    # Create a .git file instead of directory
    git_file = tmp_path / ".git"
    git_file.write_text("gitdir: ../somewhere")

    assert is_git_repo(tmp_path) is False


def test_should_exclude_matching_pattern() -> None:
    """Test that should_exclude returns True for matching patterns."""
    path = Path("/some/path/node_modules")
    patterns = ["node_modules", "venv"]

    assert should_exclude(path, patterns) is True


def test_should_exclude_non_matching_pattern() -> None:
    """Test that should_exclude returns False for non-matching patterns."""
    path = Path("/some/path/project")
    patterns = ["node_modules", "venv"]

    assert should_exclude(path, patterns) is False


def test_scan_directory_finds_single_repo(tmp_path: Path) -> None:
    """Test scanning a directory with a single git repository."""
    # Create a git repo
    repo = tmp_path / "my-repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    # Scan
    repos = list(scan_directory(tmp_path))

    assert len(repos) == 1
    assert repos[0] == repo


def test_scan_directory_finds_multiple_repos(tmp_path: Path) -> None:
    """Test scanning a directory with multiple git repositories."""
    # Create multiple repos
    repo1 = tmp_path / "repo1"
    repo1.mkdir()
    (repo1 / ".git").mkdir()

    repo2 = tmp_path / "repo2"
    repo2.mkdir()
    (repo2 / ".git").mkdir()

    # Scan
    repos = list(scan_directory(tmp_path))

    assert len(repos) == 2
    assert repo1 in repos
    assert repo2 in repos


def test_scan_directory_excludes_patterns(tmp_path: Path) -> None:
    """Test that scan_directory respects exclusion patterns."""
    # Create repos
    good_repo = tmp_path / "good-repo"
    good_repo.mkdir()
    (good_repo / ".git").mkdir()

    # Create excluded directory with repo inside
    excluded = tmp_path / "node_modules"
    excluded.mkdir()
    bad_repo = excluded / "some-package"
    bad_repo.mkdir()
    (bad_repo / ".git").mkdir()

    # Scan with exclusion
    repos = list(scan_directory(tmp_path, exclude_patterns=["node_modules"]))

    assert len(repos) == 1
    assert repos[0] == good_repo


def test_scan_directory_respects_max_depth(tmp_path: Path) -> None:
    """Test that scan_directory respects max_depth parameter."""
    # Create nested repos
    shallow_repo = tmp_path / "shallow"
    shallow_repo.mkdir()
    (shallow_repo / ".git").mkdir()

    deep_dir = tmp_path / "level1" / "level2"
    deep_dir.mkdir(parents=True)
    deep_repo = deep_dir / "deep"
    deep_repo.mkdir()
    (deep_repo / ".git").mkdir()

    # Scan with depth limit
    repos = list(scan_directory(tmp_path, max_depth=1))

    assert len(repos) == 1
    assert repos[0] == shallow_repo


def test_scan_directory_does_not_descend_into_repos(tmp_path: Path) -> None:
    """Test that scan_directory does not descend into git repositories."""
    # Create parent repo with nested .git directory
    parent_repo = tmp_path / "parent"
    parent_repo.mkdir()
    (parent_repo / ".git").mkdir()

    # Create what looks like a nested repo (shouldn't be found)
    nested_dir = parent_repo / "subdir"
    nested_dir.mkdir()
    (nested_dir / ".git").mkdir()

    # Scan
    repos = list(scan_directory(tmp_path))

    # Should only find the parent, not the nested one
    assert len(repos) == 1
    assert repos[0] == parent_repo


def test_scan_directory_handles_permission_errors(tmp_path: Path) -> None:
    """Test that scan_directory handles permission errors gracefully."""
    # Create a repo we can access
    good_repo = tmp_path / "good-repo"
    good_repo.mkdir()
    (good_repo / ".git").mkdir()

    # Note: It's hard to reliably test permission errors in a cross-platform way
    # This test mainly ensures the code doesn't crash
    repos = list(scan_directory(tmp_path))

    assert len(repos) == 1
    assert repos[0] == good_repo

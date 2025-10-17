"""Tests for git_operations module."""

from pathlib import Path
from unittest.mock import patch

from gittyup.git_operations import (
    get_current_branch,
    has_uncommitted_changes,
    pull_repository,
    run_git_command,
)
from gittyup.models import RepoState, UpdateStrategy


def test_run_git_command_success() -> None:
    """Test running a successful git command."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "success output"
        mock_run.return_value.stderr = ""

        returncode, stdout, stderr = run_git_command(Path("/tmp/repo"), ["status"])

        assert returncode == 0
        assert stdout == "success output"
        assert stderr == ""


def test_run_git_command_failure() -> None:
    """Test running a failing git command."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "error message"

        returncode, stdout, stderr = run_git_command(Path("/tmp/repo"), ["status"])

        assert returncode == 1
        assert stdout == ""
        assert stderr == "error message"


def test_run_git_command_timeout() -> None:
    """Test that run_git_command handles timeouts."""
    with patch("subprocess.run") as mock_run:
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("git", 60)

        returncode, stdout, stderr = run_git_command(Path("/tmp/repo"), ["status"])

        assert returncode == 1
        assert "timed out" in stderr.lower()


def test_get_current_branch_success() -> None:
    """Test getting the current branch name."""
    with patch("gittyup.git_operations.run_git_command") as mock_run:
        mock_run.return_value = (0, "main", "")

        branch = get_current_branch(Path("/tmp/repo"))

        assert branch == "main"


def test_get_current_branch_detached_head() -> None:
    """Test getting branch when in detached HEAD state."""
    with patch("gittyup.git_operations.run_git_command") as mock_run:
        mock_run.return_value = (0, "", "")

        branch = get_current_branch(Path("/tmp/repo"))

        assert branch is None


def test_has_uncommitted_changes_clean() -> None:
    """Test checking for uncommitted changes in a clean repo."""
    with patch("gittyup.git_operations.run_git_command") as mock_run:
        mock_run.return_value = (0, "", "")

        result = has_uncommitted_changes(Path("/tmp/repo"))

        assert result is False


def test_has_uncommitted_changes_dirty() -> None:
    """Test checking for uncommitted changes in a dirty repo."""
    with patch("gittyup.git_operations.run_git_command") as mock_run:
        mock_run.return_value = (0, " M file.txt\n?? newfile.txt", "")

        result = has_uncommitted_changes(Path("/tmp/repo"))

        assert result is True


def test_pull_repository_success() -> None:
    """Test successfully pulling a repository."""
    with (
        patch("gittyup.git_operations.get_current_branch") as mock_branch,
        patch("gittyup.git_operations.has_uncommitted_changes") as mock_changes,
        patch("gittyup.git_operations.run_git_command") as mock_run,
    ):
        mock_branch.return_value = "main"
        mock_changes.return_value = False
        mock_run.return_value = (0, "Already up to date.", "")

        result = pull_repository(Path("/tmp/repo"))

        assert result.state == RepoState.SUCCESS
        assert result.branch == "main"
        assert "Already up to date" in result.message
        assert result.error is None


def test_pull_repository_with_uncommitted_changes() -> None:
    """Test pulling a repository with uncommitted changes."""
    with (
        patch("gittyup.git_operations.get_current_branch") as mock_branch,
        patch("gittyup.git_operations.has_uncommitted_changes") as mock_changes,
    ):
        mock_branch.return_value = "main"
        mock_changes.return_value = True

        result = pull_repository(Path("/tmp/repo"))

        assert result.state == RepoState.SKIPPED
        assert result.has_uncommitted_changes is True
        assert "Uncommitted changes" in result.message


def test_pull_repository_failure() -> None:
    """Test pulling a repository that fails."""
    with (
        patch("gittyup.git_operations.get_current_branch") as mock_branch,
        patch("gittyup.git_operations.has_uncommitted_changes") as mock_changes,
        patch("gittyup.git_operations.run_git_command") as mock_run,
    ):
        mock_branch.return_value = "main"
        mock_changes.return_value = False
        mock_run.return_value = (1, "", "Authentication failed")

        result = pull_repository(Path("/tmp/repo"))

        assert result.state == RepoState.FAILED
        assert result.error == "Authentication failed"


def test_pull_repository_fast_forward() -> None:
    """Test pulling a repository with fast-forward updates."""
    with (
        patch("gittyup.git_operations.get_current_branch") as mock_branch,
        patch("gittyup.git_operations.has_uncommitted_changes") as mock_changes,
        patch("gittyup.git_operations.run_git_command") as mock_run,
    ):
        mock_branch.return_value = "main"
        mock_changes.return_value = False
        mock_run.return_value = (
            0,
            (
                "Updating 1234abc..5678def\nFast-forward\n"
                " 3 files changed, 42 insertions(+)"
            ),
            "",
        )

        result = pull_repository(Path("/tmp/repo"))

        assert result.state == RepoState.SUCCESS
        assert "Fast-forward" in result.message
        assert result.commits_pulled > 0


def test_pull_repository_with_different_strategies() -> None:
    """Test pulling with different update strategies."""
    with (
        patch("gittyup.git_operations.get_current_branch") as mock_branch,
        patch("gittyup.git_operations.has_uncommitted_changes") as mock_changes,
        patch("gittyup.git_operations.run_git_command") as mock_run,
    ):
        mock_branch.return_value = "main"
        mock_changes.return_value = False
        mock_run.return_value = (0, "Already up to date.", "")

        # Test fetch strategy
        result = pull_repository(Path("/tmp/repo"), UpdateStrategy.FETCH)
        assert result.state == RepoState.SUCCESS
        mock_run.assert_called_with(Path("/tmp/repo"), ["fetch", "--all"])

        # Test rebase strategy
        result = pull_repository(Path("/tmp/repo"), UpdateStrategy.REBASE)
        assert result.state == RepoState.SUCCESS
        mock_run.assert_called_with(Path("/tmp/repo"), ["pull", "--rebase"])


# Async tests


async def test_run_git_command_async_success() -> None:
    """Test running a successful async git command."""
    from unittest.mock import AsyncMock

    from gittyup.git_operations import run_git_command_async

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"success output", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        returncode, stdout, stderr = await run_git_command_async(
            Path("/tmp/repo"), ["status"]
        )

        assert returncode == 0
        assert stdout == "success output"
        assert stderr == ""


async def test_run_git_command_async_timeout() -> None:
    """Test that async git command handles timeouts."""
    from unittest.mock import AsyncMock, Mock

    from gittyup.git_operations import run_git_command_async

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.side_effect = TimeoutError()
        mock_process.kill = Mock()  # kill() is synchronous, not async
        mock_process.wait = AsyncMock()
        mock_exec.return_value = mock_process

        returncode, stdout, stderr = await run_git_command_async(
            Path("/tmp/repo"), ["status"], timeout=1
        )

        assert returncode == 1
        assert "timed out" in stderr.lower()
        mock_process.kill.assert_called_once()


async def test_get_current_branch_async_success() -> None:
    """Test getting current branch asynchronously."""
    from gittyup.git_operations import get_current_branch_async

    with patch(
        "gittyup.git_operations.run_git_command_async", return_value=(0, "main", "")
    ):
        branch = await get_current_branch_async(Path("/tmp/repo"))
        assert branch == "main"


async def test_has_uncommitted_changes_async_clean() -> None:
    """Test checking for uncommitted changes when repo is clean."""
    from gittyup.git_operations import has_uncommitted_changes_async

    with patch(
        "gittyup.git_operations.run_git_command_async", return_value=(0, "", "")
    ):
        has_changes = await has_uncommitted_changes_async(Path("/tmp/repo"))
        assert has_changes is False


async def test_has_uncommitted_changes_async_dirty() -> None:
    """Test checking for uncommitted changes when repo is dirty."""
    from gittyup.git_operations import has_uncommitted_changes_async

    with patch(
        "gittyup.git_operations.run_git_command_async",
        return_value=(0, "M file.txt", ""),
    ):
        has_changes = await has_uncommitted_changes_async(Path("/tmp/repo"))
        assert has_changes is True


async def test_pull_repository_async_success() -> None:
    """Test pulling a repository asynchronously."""
    from gittyup.git_operations import pull_repository_async

    with (
        patch("gittyup.git_operations.get_current_branch_async", return_value="main"),
        patch(
            "gittyup.git_operations.has_uncommitted_changes_async", return_value=False
        ),
        patch(
            "gittyup.git_operations.run_git_command_async",
            return_value=(0, "Already up to date.", ""),
        ),
    ):
        result = await pull_repository_async(Path("/tmp/repo"))

        assert result.state == RepoState.SUCCESS
        assert result.branch == "main"
        assert "up to date" in result.message.lower()


async def test_pull_repository_async_with_uncommitted_changes() -> None:
    """Test pulling a repository with uncommitted changes asynchronously."""
    from gittyup.git_operations import pull_repository_async

    with (
        patch("gittyup.git_operations.get_current_branch_async", return_value="main"),
        patch(
            "gittyup.git_operations.has_uncommitted_changes_async", return_value=True
        ),
    ):
        result = await pull_repository_async(Path("/tmp/repo"))

        assert result.state == RepoState.SKIPPED
        assert result.has_uncommitted_changes is True

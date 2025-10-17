"""Git command execution and operations."""

import asyncio
import subprocess
from pathlib import Path

from gittyup import constants
from gittyup.models import RepoState, RepoStatus, UpdateStrategy


def run_git_command(
    repo_path: Path, args: list[str], timeout: int = constants.GIT_COMMAND_TIMEOUT
) -> tuple[int, str, str]:
    """
    Run a git command in a repository.

    Args:
        repo_path: Path to the repository
        args: Git command arguments (without 'git')
        timeout: Command timeout in seconds

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", f"Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return 1, "", "Git command not found. Please ensure Git is installed."
    except Exception as e:
        return 1, "", str(e)


def get_current_branch(repo_path: Path) -> str | None:
    """
    Get the current branch of a repository.

    Args:
        repo_path: Path to the repository

    Returns:
        Branch name or None if detached HEAD or error
    """
    returncode, stdout, _ = run_git_command(repo_path, ["branch", "--show-current"])
    if returncode == 0 and stdout:
        return stdout
    return None


def has_uncommitted_changes(repo_path: Path) -> bool:
    """
    Check if a repository has uncommitted changes.

    Args:
        repo_path: Path to the repository

    Returns:
        True if there are uncommitted changes
    """
    returncode, stdout, _ = run_git_command(repo_path, ["status", "--porcelain"])
    return returncode == 0 and bool(stdout)


def pull_repository(
    repo_path: Path, strategy: UpdateStrategy = UpdateStrategy.PULL
) -> RepoStatus:
    """
    Pull updates for a repository.

    Args:
        repo_path: Path to the repository
        strategy: Update strategy to use

    Returns:
        RepoStatus object with operation results
    """
    # Get current branch
    branch = get_current_branch(repo_path)

    # Check for uncommitted changes
    has_changes = has_uncommitted_changes(repo_path)

    if has_changes:
        return RepoStatus(
            path=repo_path,
            state=RepoState.SKIPPED,
            branch=branch,
            message="Uncommitted changes detected",
            has_uncommitted_changes=True,
        )

    # Execute pull based on strategy
    match strategy:
        case UpdateStrategy.PULL:
            args = ["pull", "--all"]
        case UpdateStrategy.FETCH:
            args = ["fetch", "--all"]
        case UpdateStrategy.REBASE:
            args = ["pull", "--rebase"]

    returncode, stdout, stderr = run_git_command(repo_path, args)

    if returncode != 0:
        return RepoStatus(
            path=repo_path,
            state=RepoState.FAILED,
            branch=branch,
            message="Pull failed",
            error=stderr or stdout,
            has_uncommitted_changes=has_changes,
        )

    # Parse output to determine if updates were made
    message = "Already up to date"
    commits_pulled = 0

    if stdout:
        if "Already up to date" in stdout or "Already up-to-date" in stdout:
            message = "Already up to date"
        elif "Fast-forward" in stdout:
            # Try to count commits (rough estimate)
            lines = stdout.split("\n")
            file_changes = [line for line in lines if "changed" in line.lower()]
            if file_changes:
                message = f"Fast-forward: {file_changes[0]}"
            else:
                message = "Fast-forward"
            commits_pulled = 1
        else:
            message = "Updated"
            commits_pulled = 1

    return RepoStatus(
        path=repo_path,
        state=RepoState.SUCCESS,
        branch=branch,
        message=message,
        has_uncommitted_changes=False,
        commits_pulled=commits_pulled,
    )


# Async versions for parallel processing


async def run_git_command_async(
    repo_path: Path, args: list[str], timeout: int = constants.GIT_COMMAND_TIMEOUT
) -> tuple[int, str, str]:
    """
    Run a git command asynchronously in a repository.

    Args:
        repo_path: Path to the repository
        args: Git command arguments (without 'git')
        timeout: Command timeout in seconds

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        process = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            stdout = stdout_bytes.decode("utf-8").strip()
            stderr = stderr_bytes.decode("utf-8").strip()
            return process.returncode or 0, stdout, stderr
        except TimeoutError:
            process.kill()
            await process.wait()
            return 1, "", f"Command timed out after {timeout} seconds"

    except FileNotFoundError:
        return 1, "", "Git command not found. Please ensure Git is installed."
    except Exception as e:
        return 1, "", str(e)


async def get_current_branch_async(repo_path: Path) -> str | None:
    """
    Get the current branch of a repository asynchronously.

    Args:
        repo_path: Path to the repository

    Returns:
        Branch name or None if detached HEAD or error
    """
    returncode, stdout, _ = await run_git_command_async(
        repo_path, ["branch", "--show-current"]
    )
    if returncode == 0 and stdout:
        return stdout
    return None


async def has_uncommitted_changes_async(repo_path: Path) -> bool:
    """
    Check if a repository has uncommitted changes asynchronously.

    Args:
        repo_path: Path to the repository

    Returns:
        True if there are uncommitted changes
    """
    returncode, stdout, _ = await run_git_command_async(
        repo_path, ["status", "--porcelain"]
    )
    return returncode == 0 and bool(stdout)


async def pull_repository_async(
    repo_path: Path, strategy: UpdateStrategy = UpdateStrategy.PULL
) -> RepoStatus:
    """
    Pull updates for a repository asynchronously.

    Args:
        repo_path: Path to the repository
        strategy: Update strategy to use

    Returns:
        RepoStatus object with operation results
    """
    # Get current branch
    branch = await get_current_branch_async(repo_path)

    # Check for uncommitted changes
    has_changes = await has_uncommitted_changes_async(repo_path)

    if has_changes:
        return RepoStatus(
            path=repo_path,
            state=RepoState.SKIPPED,
            branch=branch,
            message="Uncommitted changes detected",
            has_uncommitted_changes=True,
        )

    # Execute pull based on strategy
    match strategy:
        case UpdateStrategy.PULL:
            args = ["pull", "--all"]
        case UpdateStrategy.FETCH:
            args = ["fetch", "--all"]
        case UpdateStrategy.REBASE:
            args = ["pull", "--rebase"]

    returncode, stdout, stderr = await run_git_command_async(repo_path, args)

    if returncode != 0:
        return RepoStatus(
            path=repo_path,
            state=RepoState.FAILED,
            branch=branch,
            message="Pull failed",
            error=stderr or stdout,
            has_uncommitted_changes=has_changes,
        )

    # Parse output to determine if updates were made
    message = "Already up to date"
    commits_pulled = 0

    if stdout:
        if "Already up to date" in stdout or "Already up-to-date" in stdout:
            message = "Already up to date"
        elif "Fast-forward" in stdout:
            # Try to count commits (rough estimate)
            lines = stdout.split("\n")
            file_changes = [line for line in lines if "changed" in line.lower()]
            if file_changes:
                message = f"Fast-forward: {file_changes[0]}"
            else:
                message = "Fast-forward"
            commits_pulled = 1
        else:
            message = "Updated"
            commits_pulled = 1

    return RepoStatus(
        path=repo_path,
        state=RepoState.SUCCESS,
        branch=branch,
        message=message,
        has_uncommitted_changes=False,
        commits_pulled=commits_pulled,
    )

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


def stash_changes(repo_path: Path) -> tuple[bool, str]:
    """
    Stash uncommitted changes in a repository.

    Args:
        repo_path: Path to the repository

    Returns:
        Tuple of (success, message)
    """
    returncode, stdout, stderr = run_git_command(repo_path, ["stash", "push", "-u"])
    if returncode == 0:
        if "No local changes to save" in stdout:
            return True, "No changes to stash"
        return True, "Changes stashed"
    return False, stderr or stdout


def pop_stash(repo_path: Path) -> tuple[bool, str]:
    """
    Pop the most recent stash in a repository.

    Args:
        repo_path: Path to the repository

    Returns:
        Tuple of (success, message)
    """
    returncode, stdout, stderr = run_git_command(repo_path, ["stash", "pop"])
    if returncode == 0:
        return True, "Stash popped successfully"
    return False, stderr or stdout


def pull_repository(  # noqa: C901
    repo_path: Path,
    strategy: UpdateStrategy = UpdateStrategy.PULL,
    stash_before_pull: bool = False,
) -> RepoStatus:
    """
    Pull updates for a repository.

    Args:
        repo_path: Path to the repository
        strategy: Update strategy to use
        stash_before_pull: If True, stash changes before pulling and pop after

    Returns:
        RepoStatus object with operation results
    """
    # Get current branch
    branch = get_current_branch(repo_path)

    # Check for uncommitted changes
    has_changes = has_uncommitted_changes(repo_path)

    # Track if we stashed changes
    stashed = False

    if has_changes:
        if stash_before_pull:
            # Try to stash changes
            success, message = stash_changes(repo_path)
            if not success:
                return RepoStatus(
                    path=repo_path,
                    state=RepoState.FAILED,
                    branch=branch,
                    message="Failed to stash changes",
                    error=message,
                    has_uncommitted_changes=True,
                )
            stashed = True
        else:
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

    # Pop stash if we stashed changes
    if stashed:
        pop_success, pop_message = pop_stash(repo_path)
        if not pop_success:
            return RepoStatus(
                path=repo_path,
                state=RepoState.FAILED,
                branch=branch,
                message="Pull succeeded but failed to pop stash",
                error=pop_message,
                has_uncommitted_changes=True,
            )
        if message == "Already up to date":
            message = "Stashed, pulled, and restored changes"
        else:
            message = f"{message} (stash restored)"

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


async def stash_changes_async(repo_path: Path) -> tuple[bool, str]:
    """
    Stash uncommitted changes in a repository asynchronously.

    Args:
        repo_path: Path to the repository

    Returns:
        Tuple of (success, message)
    """
    returncode, stdout, stderr = await run_git_command_async(
        repo_path, ["stash", "push", "-u"]
    )
    if returncode == 0:
        if "No local changes to save" in stdout:
            return True, "No changes to stash"
        return True, "Changes stashed"
    return False, stderr or stdout


async def pop_stash_async(repo_path: Path) -> tuple[bool, str]:
    """
    Pop the most recent stash in a repository asynchronously.

    Args:
        repo_path: Path to the repository

    Returns:
        Tuple of (success, message)
    """
    returncode, stdout, stderr = await run_git_command_async(
        repo_path, ["stash", "pop"]
    )
    if returncode == 0:
        return True, "Stash popped successfully"
    return False, stderr or stdout


async def pull_repository_async(  # noqa: C901
    repo_path: Path,
    strategy: UpdateStrategy = UpdateStrategy.PULL,
    stash_before_pull: bool = False,
) -> RepoStatus:
    """
    Pull updates for a repository asynchronously.

    Args:
        repo_path: Path to the repository
        strategy: Update strategy to use
        stash_before_pull: If True, stash changes before pulling and pop after

    Returns:
        RepoStatus object with operation results
    """
    # Get current branch
    branch = await get_current_branch_async(repo_path)

    # Check for uncommitted changes
    has_changes = await has_uncommitted_changes_async(repo_path)

    # Track if we stashed changes
    stashed = False

    if has_changes:
        if stash_before_pull:
            # Try to stash changes
            success, message = await stash_changes_async(repo_path)
            if not success:
                return RepoStatus(
                    path=repo_path,
                    state=RepoState.FAILED,
                    branch=branch,
                    message="Failed to stash changes",
                    error=message,
                    has_uncommitted_changes=True,
                )
            stashed = True
        else:
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

    # Pop stash if we stashed changes
    if stashed:
        pop_success, pop_message = await pop_stash_async(repo_path)
        if not pop_success:
            return RepoStatus(
                path=repo_path,
                state=RepoState.FAILED,
                branch=branch,
                message="Pull succeeded but failed to pop stash",
                error=pop_message,
                has_uncommitted_changes=True,
            )
        if message == "Already up to date":
            message = "Stashed, pulled, and restored changes"
        else:
            message = f"{message} (stash restored)"

    return RepoStatus(
        path=repo_path,
        state=RepoState.SUCCESS,
        branch=branch,
        message=message,
        has_uncommitted_changes=False,
        commits_pulled=commits_pulled,
    )

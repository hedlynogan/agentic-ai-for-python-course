"""Tests for models module."""

from pathlib import Path

from gittyup.models import OutputFormat, RepoState, RepoStatus, SummaryStats


def test_repo_status_to_dict() -> None:
    """Test converting RepoStatus to dictionary."""
    status = RepoStatus(
        path=Path("/tmp/test-repo"),
        state=RepoState.SUCCESS,
        branch="main",
        message="Already up to date",
        error=None,
        has_uncommitted_changes=False,
        commits_pulled=0,
    )

    result = status.to_dict()

    assert result["path"] == "/tmp/test-repo"
    assert result["state"] == "success"
    assert result["branch"] == "main"
    assert result["message"] == "Already up to date"
    assert result["error"] is None
    assert result["has_uncommitted_changes"] is False
    assert result["commits_pulled"] == 0


def test_repo_status_to_dict_with_error() -> None:
    """Test converting RepoStatus with error to dictionary."""
    status = RepoStatus(
        path=Path("/tmp/failed-repo"),
        state=RepoState.FAILED,
        branch="develop",
        message="Pull failed",
        error="fatal: unable to access remote",
        has_uncommitted_changes=False,
        commits_pulled=0,
    )

    result = status.to_dict()

    assert result["path"] == "/tmp/failed-repo"
    assert result["state"] == "failed"
    assert result["error"] == "fatal: unable to access remote"


def test_summary_stats_to_dict() -> None:
    """Test converting SummaryStats to dictionary."""
    stats = SummaryStats(
        repos_found=5,
        repos_updated=3,
        repos_skipped=1,
        repos_failed=1,
        duration_seconds=12.345,
    )

    # Add some results
    stats.results = [
        RepoStatus(
            path=Path("/tmp/repo1"),
            state=RepoState.SUCCESS,
            branch="main",
            message="Updated",
        ),
        RepoStatus(
            path=Path("/tmp/repo2"),
            state=RepoState.SKIPPED,
            branch="develop",
            message="Uncommitted changes",
        ),
    ]

    result = stats.to_dict()

    assert result["summary"]["repos_found"] == 5
    assert result["summary"]["repos_updated"] == 3
    assert result["summary"]["repos_skipped"] == 1
    assert result["summary"]["repos_failed"] == 1
    assert result["summary"]["duration_seconds"] == 12.35
    assert len(result["repositories"]) == 2
    assert result["repositories"][0]["path"] == "/tmp/repo1"
    assert result["repositories"][1]["path"] == "/tmp/repo2"


def test_output_format_enum() -> None:
    """Test OutputFormat enum values."""
    assert OutputFormat.TEXT.value == "text"
    assert OutputFormat.JSON.value == "json"

"""Tests for reporter module."""

from pathlib import Path

import pytest

from gittyup.models import RepoState, RepoStatus, SummaryStats
from gittyup.reporter import (
    format_with_color,
    print_header,
    print_repos_found,
    report_repo_processing,
    report_summary,
)


def test_format_with_color_enabled() -> None:
    """Test formatting text with color enabled."""
    from gittyup import constants

    result = format_with_color("test", constants.COLOR_SUCCESS, no_color=False)

    assert constants.COLOR_SUCCESS in result
    assert "test" in result


def test_format_with_color_disabled() -> None:
    """Test formatting text with color disabled."""
    from gittyup import constants

    result = format_with_color("test", constants.COLOR_SUCCESS, no_color=True)

    assert result == "test"
    assert constants.COLOR_SUCCESS not in result


def test_print_header(capsys: pytest.CaptureFixture) -> None:
    """Test printing the header."""
    print_header(Path("/tmp/test"), no_color=True)

    captured = capsys.readouterr()
    assert "Gitty Up" in captured.out
    assert "/tmp/test" in captured.out


def test_print_repos_found_single(capsys: pytest.CaptureFixture) -> None:
    """Test printing repos found message with single repo."""
    print_repos_found(1, no_color=True)

    captured = capsys.readouterr()
    assert "1" in captured.out
    assert "repository" in captured.out
    assert "repositories" not in captured.out  # singular form


def test_print_repos_found_multiple(capsys: pytest.CaptureFixture) -> None:
    """Test printing repos found message with multiple repos."""
    print_repos_found(5, no_color=True)

    captured = capsys.readouterr()
    assert "5" in captured.out
    assert "repositories" in captured.out


def test_report_repo_processing_success(capsys: pytest.CaptureFixture) -> None:
    """Test reporting a successful repository update."""
    result = RepoStatus(
        path=Path("/tmp/my-repo"),
        state=RepoState.SUCCESS,
        branch="main",
        message="Already up to date",
    )

    report_repo_processing(result, verbose=False, no_color=True)

    captured = capsys.readouterr()
    assert "my-repo" in captured.out
    assert "main" in captured.out
    assert "Already up to date" in captured.out


def test_report_repo_processing_skipped(capsys: pytest.CaptureFixture) -> None:
    """Test reporting a skipped repository."""
    result = RepoStatus(
        path=Path("/tmp/my-repo"),
        state=RepoState.SKIPPED,
        branch="develop",
        message="Uncommitted changes",
        has_uncommitted_changes=True,
    )

    report_repo_processing(result, verbose=False, no_color=True)

    captured = capsys.readouterr()
    assert "my-repo" in captured.out
    assert "Uncommitted changes" in captured.out


def test_report_repo_processing_failed(capsys: pytest.CaptureFixture) -> None:
    """Test reporting a failed repository update."""
    result = RepoStatus(
        path=Path("/tmp/my-repo"),
        state=RepoState.FAILED,
        branch="main",
        message="Pull failed",
        error="Authentication failed",
    )

    report_repo_processing(result, verbose=False, no_color=True)

    captured = capsys.readouterr()
    assert "my-repo" in captured.out
    assert "Pull failed" in captured.out


def test_report_repo_processing_verbose_with_error(
    capsys: pytest.CaptureFixture,
) -> None:
    """Test reporting with verbose mode shows error details."""
    result = RepoStatus(
        path=Path("/tmp/my-repo"),
        state=RepoState.FAILED,
        branch="main",
        message="Pull failed",
        error="Authentication failed: invalid credentials",
    )

    report_repo_processing(result, verbose=True, no_color=True)

    captured = capsys.readouterr()
    assert "my-repo" in captured.out
    assert "Authentication failed" in captured.out


def test_report_summary(capsys: pytest.CaptureFixture) -> None:
    """Test printing the summary statistics."""
    stats = SummaryStats(
        repos_found=10,
        repos_updated=7,
        repos_skipped=2,
        repos_failed=1,
        duration_seconds=5.5,
    )

    report_summary(stats, no_color=True)

    captured = capsys.readouterr()
    output = captured.out

    assert "Summary" in output
    assert "10" in output  # repos found
    assert "7" in output  # repos updated
    assert "2" in output  # repos skipped
    assert "1" in output  # repos failed
    assert "5.5" in output  # duration


def test_report_summary_no_failures(capsys: pytest.CaptureFixture) -> None:
    """Test summary with no failures or skips."""
    stats = SummaryStats(
        repos_found=5,
        repos_updated=5,
        repos_skipped=0,
        repos_failed=0,
        duration_seconds=3.2,
    )

    report_summary(stats, no_color=True)

    captured = capsys.readouterr()
    output = captured.out

    assert "5" in output
    assert "Successfully updated: 5" in output
    # Skipped and Failed sections might not appear or be 0

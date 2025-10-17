"""Data models for Gitty Up."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class UpdateStrategy(Enum):
    """Git update strategies."""

    PULL = "pull"
    FETCH = "fetch"
    REBASE = "rebase"


class RepoState(Enum):
    """State of a repository after processing."""

    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"
    DRY_RUN = "dry_run"


@dataclass
class RepoStatus:
    """Status of a single repository after processing."""

    path: Path
    state: RepoState
    branch: str | None = None
    message: str = ""
    error: str | None = None
    has_uncommitted_changes: bool = False
    commits_pulled: int = 0


@dataclass
class ScanConfig:
    """Configuration for scanning and updating repositories."""

    root_path: Path
    max_depth: int | None = None
    exclude_patterns: list[str] = field(default_factory=list)
    strategy: UpdateStrategy = UpdateStrategy.PULL
    dry_run: bool = False
    verbose: bool = False
    quiet: bool = False
    no_color: bool = False
    max_workers: int = 4


@dataclass
class SummaryStats:
    """Summary statistics for a scan operation."""

    repos_found: int = 0
    repos_updated: int = 0
    repos_skipped: int = 0
    repos_failed: int = 0
    duration_seconds: float = 0.0
    results: list[RepoStatus] = field(default_factory=list)

    def add_result(self, result: RepoStatus) -> None:
        """Add a repository result to the summary."""
        self.results.append(result)
        match result.state:
            case RepoState.SUCCESS:
                self.repos_updated += 1
            case RepoState.SKIPPED:
                self.repos_skipped += 1
            case RepoState.FAILED:
                self.repos_failed += 1

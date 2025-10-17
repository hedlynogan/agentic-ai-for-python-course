"""Command-line interface for Gitty Up."""

import argparse
import asyncio
import sys
import time
from pathlib import Path

from gittyup import __version__, config, constants, git_operations, reporter
from gittyup.models import RepoState, RepoStatus, ScanConfig, SummaryStats
from gittyup.scanner import scan_directory


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="gittyup",
        description=(
            "Automatically discover and update all Git repositories in a directory tree"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  gittyup                    # Scan current directory
  gittyup ~/projects         # Scan specific directory
  gittyup --dry-run          # Preview what would be done
  gittyup --max-depth 2      # Limit traversal depth
  gittyup -w                 # Verbose output
        """,
    )

    # Positional arguments
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        type=Path,
        help="Root directory to scan (default: current directory)",
    )

    # Operation modes
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be done without making changes",
    )

    # Filtering & Traversal
    parser.add_argument(
        "--max-depth",
        type=int,
        metavar="DEPTH",
        help="Maximum directory depth to traverse",
    )

    parser.add_argument(
        "--exclude",
        action="append",
        metavar="PATTERN",
        dest="exclude_patterns",
        help="Exclude directories matching pattern (can be repeated)",
    )

    # Git operations
    parser.add_argument(
        "--strategy",
        choices=["pull", "fetch", "rebase"],
        default="pull",
        help="Update strategy (default: pull)",
    )

    # Output control
    parser.add_argument(
        "--wordy",
        "-w",
        action="count",
        default=0,
        dest="verbose",
        help="Increase output verbosity",
    )

    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Minimize output (errors only)"
    )

    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    # Performance
    parser.add_argument(
        "--workers",
        type=int,
        metavar="N",
        help="Number of concurrent workers (default: 4)",
    )

    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Disable parallel processing (equivalent to --workers 1)",
    )

    # Configuration
    parser.add_argument(
        "--no-config",
        action="store_true",
        help="Ignore configuration files",
    )

    # Info
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    return parser


def validate_args(args: argparse.Namespace) -> str | None:
    """
    Validate parsed arguments.

    Args:
        args: Parsed arguments

    Returns:
        Error message if validation fails, None otherwise
    """
    # Check if path exists
    if not args.path.exists():
        return f"Path does not exist: {args.path}"

    # Check if path is a directory
    if not args.path.is_dir():
        return f"Path is not a directory: {args.path}"

    # Check if max_depth is valid
    if args.max_depth is not None and args.max_depth < 0:
        return "Max depth must be non-negative"

    # Check if workers is valid
    if args.workers is not None and args.workers < 1:
        return "Workers must be at least 1"

    # Check for conflicting options
    if args.sequential and args.workers is not None:
        return "Cannot specify both --sequential and --workers"

    return None


def process_repositories(config: ScanConfig) -> SummaryStats:
    """
    Process all repositories according to configuration.

    Args:
        config: Scan configuration

    Returns:
        Summary statistics
    """
    stats = SummaryStats()

    # Find all repositories
    repos = list(
        scan_directory(
            config.root_path,
            max_depth=config.max_depth,
            exclude_patterns=config.exclude_patterns or constants.DEFAULT_EXCLUDES,
        )
    )

    stats.repos_found = len(repos)

    if not config.quiet:
        reporter.print_repos_found(stats.repos_found, config.no_color)

    # Early return if no repos found
    if stats.repos_found == 0:
        return stats

    # Print section header
    if not config.quiet:
        if config.dry_run:
            reporter.print_section_header(
                "Dry run (no changes will be made):", config.no_color
            )
        else:
            reporter.print_section_header("Updating repositories...", config.no_color)

    # Process each repository
    for repo in repos:
        if config.dry_run:
            # In dry-run mode, just check status
            branch = git_operations.get_current_branch(repo)
            has_changes = git_operations.has_uncommitted_changes(repo)

            from gittyup.models import RepoState, RepoStatus

            message = (
                "Would pull" if not has_changes else "Would skip (uncommitted changes)"
            )
            result = RepoStatus(
                path=repo,
                state=RepoState.DRY_RUN,
                branch=branch,
                message=message,
                has_uncommitted_changes=has_changes,
            )
        else:
            # Actually pull the repository
            result = git_operations.pull_repository(repo, config.strategy)

        stats.add_result(result)

        if not config.quiet:
            reporter.report_repo_processing(result, config.verbose, config.no_color)

    return stats


async def process_repository_async(
    repo: Path, config: ScanConfig
) -> tuple[RepoStatus, bool]:
    """
    Process a single repository asynchronously.

    Args:
        repo: Path to repository
        config: Scan configuration

    Returns:
        Tuple of (RepoStatus, should_print) where should_print indicates if output
        should be shown immediately
    """
    if config.dry_run:
        # In dry-run mode, just check status
        branch = await git_operations.get_current_branch_async(repo)
        has_changes = await git_operations.has_uncommitted_changes_async(repo)

        message = (
            "Would pull" if not has_changes else "Would skip (uncommitted changes)"
        )
        result = RepoStatus(
            path=repo,
            state=RepoState.DRY_RUN,
            branch=branch,
            message=message,
            has_uncommitted_changes=has_changes,
        )
    else:
        # Actually pull the repository
        result = await git_operations.pull_repository_async(repo, config.strategy)

    return result, not config.quiet


async def process_repositories_async(scan_config: ScanConfig) -> SummaryStats:
    """
    Process all repositories asynchronously with controlled concurrency.

    Args:
        scan_config: Scan configuration

    Returns:
        Summary statistics
    """
    stats = SummaryStats()

    # Find all repositories
    repos = list(
        scan_directory(
            scan_config.root_path,
            max_depth=scan_config.max_depth,
            exclude_patterns=scan_config.exclude_patterns or constants.DEFAULT_EXCLUDES,
        )
    )

    stats.repos_found = len(repos)

    if not scan_config.quiet:
        reporter.print_repos_found(stats.repos_found, scan_config.no_color)

    # Early return if no repos found
    if stats.repos_found == 0:
        return stats

    # Print section header
    if not scan_config.quiet:
        if scan_config.dry_run:
            reporter.print_section_header(
                "Dry run (no changes will be made):", scan_config.no_color
            )
        else:
            reporter.print_section_header(
                "Updating repositories...", scan_config.no_color
            )

    # Create a semaphore to limit concurrent operations
    semaphore = asyncio.Semaphore(scan_config.max_workers)

    async def process_with_semaphore(repo: Path) -> RepoStatus:
        async with semaphore:
            result, should_print = await process_repository_async(repo, scan_config)
            if should_print:
                reporter.report_repo_processing(
                    result, scan_config.verbose, scan_config.no_color
                )
            return result

    # Process all repositories concurrently with controlled concurrency
    results = await asyncio.gather(
        *[process_with_semaphore(repo) for repo in repos], return_exceptions=True
    )

    # Add results to stats
    for result in results:
        if isinstance(result, Exception):
            # Handle unexpected exceptions
            continue
        stats.add_result(result)

    return stats


def main() -> int:
    """
    Main entry point for the CLI.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    args = parser.parse_args()

    # Validate arguments
    error = validate_args(args)
    if error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    # Load configuration from files (unless --no-config specified)
    file_config = {} if args.no_config else config.load_config()

    # Merge CLI args with file config (CLI takes precedence)
    cli_args = {
        "max_depth": args.max_depth,
        "exclude": args.exclude_patterns,
        "strategy": args.strategy,
        "verbose": args.verbose > 0 if args.verbose > 0 else None,
        "no_color": args.no_color if args.no_color else None,
        "max_workers": (
            1 if args.sequential else args.workers if args.workers else None
        ),
    }
    merged_config = config.merge_config_with_args(file_config, cli_args)

    # Parse strategy
    strategy = config.parse_strategy(merged_config.get("strategy", "pull"))

    # Handle exclude patterns - merge file config with CLI args
    exclude_patterns = merged_config.get("exclude", constants.DEFAULT_EXCLUDES)
    if args.exclude_patterns:
        # If CLI patterns provided, add them to the file config patterns
        exclude_patterns = list(set(exclude_patterns + args.exclude_patterns))

    # Build configuration
    scan_config = ScanConfig(
        root_path=args.path.resolve(),
        max_depth=merged_config.get("max_depth"),
        exclude_patterns=exclude_patterns,
        strategy=strategy,
        dry_run=args.dry_run,
        verbose=merged_config.get("verbose", False),
        quiet=args.quiet,
        no_color=merged_config.get("no_color", False),
        max_workers=merged_config.get("max_workers", constants.DEFAULT_MAX_WORKERS),
    )

    # Initialize colors
    reporter.initialize_colors(scan_config.no_color)

    # Print header
    if not scan_config.quiet:
        reporter.print_header(scan_config.root_path, scan_config.no_color)

    # Process repositories (use async for parallel, sync for sequential/single worker)
    start_time = time.time()
    if scan_config.max_workers > 1:
        stats = asyncio.run(process_repositories_async(scan_config))
    else:
        stats = process_repositories(scan_config)
    stats.duration_seconds = time.time() - start_time

    # Print summary
    if not scan_config.quiet:
        reporter.report_summary(stats, scan_config.no_color)

    # Determine exit code
    if stats.repos_found == 0:
        return 0
    if stats.repos_failed > 0:
        return 2 if stats.repos_updated > 0 else 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

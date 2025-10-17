"""Command-line interface for Gitty Up."""

import argparse
import sys
import time
from pathlib import Path

from gittyup import __version__, constants, git_operations, reporter
from gittyup.models import ScanConfig, SummaryStats, UpdateStrategy
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
            "Automatically discover and update all Git repositories "
            "in a directory tree"
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
            reporter.print_section_header(
                "Updating repositories...", config.no_color
            )

    # Process each repository
    for repo in repos:
        if config.dry_run:
            # In dry-run mode, just check status
            branch = git_operations.get_current_branch(repo)
            has_changes = git_operations.has_uncommitted_changes(repo)

            from gittyup.models import RepoState, RepoStatus

            message = (
                "Would pull"
                if not has_changes
                else "Would skip (uncommitted changes)"
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

    # Convert strategy string to enum
    strategy_map = {
        "pull": UpdateStrategy.PULL,
        "fetch": UpdateStrategy.FETCH,
        "rebase": UpdateStrategy.REBASE,
    }
    strategy = strategy_map[args.strategy]

    # Build configuration
    config = ScanConfig(
        root_path=args.path.resolve(),
        max_depth=args.max_depth,
        exclude_patterns=args.exclude_patterns,
        strategy=strategy,
        dry_run=args.dry_run,
        verbose=args.verbose > 0,
        quiet=args.quiet,
        no_color=args.no_color,
    )

    # Initialize colors
    reporter.initialize_colors(config.no_color)

    # Print header
    if not config.quiet:
        reporter.print_header(config.root_path, config.no_color)

    # Process repositories
    start_time = time.time()
    stats = process_repositories(config)
    stats.duration_seconds = time.time() - start_time

    # Print summary
    if not config.quiet:
        reporter.report_summary(stats, config.no_color)

    # Determine exit code
    if stats.repos_found == 0:
        return 0
    if stats.repos_failed > 0:
        return 2 if stats.repos_updated > 0 else 3
    return 0


if __name__ == "__main__":
    sys.exit(main())


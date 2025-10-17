"""Output formatting and reporting."""

from pathlib import Path

from colorama import init as colorama_init

from gittyup import constants
from gittyup.models import RepoState, RepoStatus, SummaryStats


def initialize_colors(no_color: bool = False) -> None:
    """
    Initialize colorama for cross-platform colored output.

    Args:
        no_color: If True, disable colored output
    """
    if no_color:
        colorama_init(strip=True, convert=False)
    else:
        colorama_init(autoreset=True)


def format_with_color(text: str, color: str, no_color: bool = False) -> str:
    """
    Format text with color.

    Args:
        text: Text to format
        color: Color code to apply
        no_color: If True, skip coloring

    Returns:
        Formatted text
    """
    if no_color:
        return text
    return f"{color}{text}{constants.COLOR_RESET}"


def print_header(root_path: Path, no_color: bool = False) -> None:
    """
    Print the startup header.

    Args:
        root_path: Root directory being scanned
        no_color: If True, disable colored output
    """
    header = f"{constants.SYMBOL_ROCKET} Gitty Up - Scanning {root_path}..."
    print(format_with_color(header, constants.COLOR_INFO, no_color))


def print_repos_found(count: int, no_color: bool = False) -> None:
    """
    Print the number of repositories found.

    Args:
        count: Number of repositories found
        no_color: If True, disable colored output
    """
    message = f"   Found {count} git {'repository' if count == 1 else 'repositories'}"
    print(format_with_color(message, constants.COLOR_INFO, no_color))
    print()


def print_section_header(text: str, no_color: bool = False) -> None:
    """
    Print a section header.

    Args:
        text: Header text
        no_color: If True, disable colored output
    """
    print(format_with_color(text, constants.COLOR_BOLD, no_color))


def report_repo_processing(
    result: RepoStatus, verbose: bool = False, no_color: bool = False
) -> None:
    """
    Report on a single repository processing result.

    Args:
        result: Repository status result
        verbose: If True, show detailed output
        no_color: If True, disable colored output
    """
    # Choose symbol and color based on state
    match result.state:
        case RepoState.SUCCESS:
            symbol = constants.SYMBOL_SUCCESS
            color = constants.COLOR_SUCCESS
        case RepoState.SKIPPED:
            symbol = constants.SYMBOL_WARNING
            color = constants.COLOR_WARNING
        case RepoState.FAILED:
            symbol = constants.SYMBOL_ERROR
            color = constants.COLOR_ERROR
        case _:
            symbol = constants.SYMBOL_INFO
            color = constants.COLOR_INFO

    # Format the repo name (use relative path if possible)
    repo_name = result.path.name

    # Build the status line
    branch_info = f" ({result.branch})" if result.branch else ""
    message = f"{symbol} {repo_name}{branch_info} - {result.message}"

    print(format_with_color(message, color, no_color))

    # Show error details if present and verbose
    if verbose and result.error:
        error_msg = f"   Error: {result.error}"
        print(format_with_color(error_msg, constants.COLOR_DIM, no_color))


def report_summary(stats: SummaryStats, no_color: bool = False) -> None:
    """
    Print the final summary statistics.

    Args:
        stats: Summary statistics to display
        no_color: If True, disable colored output
    """
    print()
    print_section_header("Summary:", no_color)

    # Repositories found
    found_msg = f"  {constants.SYMBOL_STATS} Repositories found: {stats.repos_found}"
    print(format_with_color(found_msg, constants.COLOR_INFO, no_color))

    # Successfully updated
    if stats.repos_updated > 0:
        success_msg = (
            f"  {constants.SYMBOL_SUCCESS} Successfully updated: {stats.repos_updated}"
        )
        print(format_with_color(success_msg, constants.COLOR_SUCCESS, no_color))

    # Skipped
    if stats.repos_skipped > 0:
        skipped_msg = f"  {constants.SYMBOL_WARNING} Skipped: {stats.repos_skipped}"
        print(format_with_color(skipped_msg, constants.COLOR_WARNING, no_color))

    # Failed
    if stats.repos_failed > 0:
        failed_msg = f"  {constants.SYMBOL_ERROR} Failed: {stats.repos_failed}"
        print(format_with_color(failed_msg, constants.COLOR_ERROR, no_color))

    # Duration
    duration_msg = f"  {constants.SYMBOL_CLOCK} Duration: {stats.duration_seconds:.1f}s"
    print(format_with_color(duration_msg, constants.COLOR_INFO, no_color))

# Gitty Up 🚀

A professional-grade CLI tool that automatically discovers and updates all Git repositories within a directory tree. Never forget to pull changes before starting work again!

## Features

- **Automatic Discovery**: Recursively scans directories to find all Git repositories
- **Batch Updates**: Pulls updates from all discovered repositories in one command
- **Parallel Processing**: ⚡ Updates multiple repositories concurrently for speed (configurable workers)
- **Configuration Files**: Support for `.gittyup.yaml` files for project-specific settings
- **Smart Exclusions**: Automatically skips common directories like `node_modules`, `venv`, etc.
- **Colored Output**: Beautiful, easy-to-read colored terminal output
- **Safety First**: Skips repositories with uncommitted changes to prevent conflicts
- **Stash Support**: 🆕 Optionally stash uncommitted changes before pulling and restore after
- **JSON Output**: 🆕 Machine-readable JSON output format for automation
- **Flexible**: Multiple update strategies (pull, fetch, rebase)
- **Informative**: Shows current branch and update status for each repository

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone <repo-url>
cd gittyup

# Create virtual environment and activate it
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
uv pip install -e .
# or
pip install -e .
```

### Install Dependencies

```bash
# Runtime dependencies
uv pip install -r requirements.piptools

# Development dependencies (for testing and linting)
uv pip install -r requirements-development.piptools
```

## Quick Start

```bash
# Scan and update all repos in current directory
gittyup

# Scan a specific directory
gittyup ~/projects

# Preview what would be done (dry run)
gittyup --dry-run

# Verbose output
gittyup -w

# Limit traversal depth
gittyup --max-depth 2

# Use different update strategy
gittyup --strategy fetch
```

## Usage

```
gittyup [OPTIONS] [PATH]

Arguments:
  PATH                  Root directory to scan (default: current directory)

Options:
  -n, --dry-run        Show what would be done without making changes
  --max-depth DEPTH    Maximum directory depth to traverse
  --exclude PATTERN    Exclude directories matching pattern (can be repeated)
  --strategy {pull,fetch,rebase}
                       Update strategy (default: pull)
  --stash              Stash changes before pulling, pop after
  --workers N          Number of concurrent workers (default: 4)
  --sequential         Disable parallel processing (equivalent to --workers 1)
  --no-config          Ignore configuration files
  -w, --wordy          Increase output verbosity
  -q, --quiet          Minimize output (errors only)
  --no-color           Disable colored output
  --format {text,json} Output format (default: text)
  --version            Show version information
  -h, --help           Show this help message

Examples:
  gittyup                    # Scan current directory
  gittyup ~/projects         # Scan specific directory
  gittyup --dry-run          # Preview what would be done
  gittyup --max-depth 2      # Limit traversal depth
  gittyup --workers 8        # Use 8 concurrent workers for faster updates
  gittyup --sequential       # Update repositories one at a time
  gittyup --stash            # Stash uncommitted changes before pulling
  gittyup --format json      # Output results as JSON
  gittyup -w                 # Verbose output
```

## Output Example

```
🚀 Gitty Up - Scanning /Users/dev/projects...
   Found 15 git repositories

Updating repositories...
✓ project-alpha (main) - Already up to date
✓ project-beta (develop) - Fast-forward: 3 files changed
⚠ project-gamma (feature/new) - Uncommitted changes detected
✗ project-delta (main) - Pull failed

Summary:
  📊 Repositories found: 15
  ✓ Successfully updated: 12
  ⚠ Skipped: 2
  ✗ Failed: 1
  ⏱ Duration: 8.3s
```

## Advanced Features

### Stash Support

When you have repositories with uncommitted changes, Gitty Up normally skips them to avoid conflicts. With the `--stash` flag, you can automatically stash changes before pulling and restore them after:

```bash
gittyup --stash
```

This is useful when you want to update all repositories including those with work-in-progress changes. The stash is automatically popped after pulling completes successfully.

### JSON Output

For automation and scripting, you can output results in JSON format:

```bash
gittyup --format json > results.json
```

Example JSON output:
```json
{
  "summary": {
    "repos_found": 5,
    "repos_updated": 3,
    "repos_skipped": 1,
    "repos_failed": 1,
    "duration_seconds": 8.32
  },
  "repositories": [
    {
      "path": "/path/to/repo1",
      "state": "success",
      "branch": "main",
      "message": "Already up to date",
      "error": null,
      "has_uncommitted_changes": false,
      "commits_pulled": 0
    }
  ]
}
```

## Configuration Files

Gitty Up supports configuration files for project-specific or user-wide settings. Configuration files are optional and will be automatically loaded if present.

### Configuration Precedence

1. **Command-line arguments** (highest priority)
2. **Local config**: `.gittyup.yaml` in current directory
3. **User config**: `~/.config/gittyup/config.yaml`
4. **Built-in defaults** (lowest priority)

### Example Configuration File

Create a `.gittyup.yaml` file in your project root:

```yaml
# Directory scanning
max_depth: 3
exclude:
  - node_modules
  - venv
  - .venv
  - build
  - dist

# Git operations
strategy: pull
pull_all_branches: true

# Performance
max_workers: 8

# Output
verbose: false
no_color: false
```

### Available Configuration Options

- `max_depth`: Maximum directory depth to traverse (integer or null)
- `exclude`: List of directory names to exclude
- `strategy`: Update strategy (`pull`, `fetch`, or `rebase`)
- `max_workers`: Number of concurrent workers (default: 4)
- `verbose`: Enable verbose output (boolean)
- `no_color`: Disable colored output (boolean)

### Disabling Configuration Files

Use `--no-config` to ignore all configuration files:

```bash
gittyup --no-config
```

## Default Exclusions

Gitty Up automatically skips these directories:

- `node_modules`
- `venv`, `.venv`, `env`, `.env`
- `.tox`
- `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`
- `dist`, `build`, `.eggs`
- `target` (Rust/Java)
- `vendor` (Go/PHP)

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_scanner.py
```

### Linting and Formatting

```bash
# Format code
ruff format .

# Check and fix linting issues
ruff check --fix .
```

## How It Works

1. **Load Config**: Loads configuration from files (if present) and merges with CLI arguments
2. **Scan**: Recursively traverses the specified directory tree
3. **Discover**: Identifies Git repositories by looking for `.git` directories
4. **Filter**: Applies exclusion patterns to skip unwanted directories
5. **Check**: Examines each repository for uncommitted changes
6. **Update**: Executes `git pull` (or chosen strategy) on clean repositories concurrently
7. **Report**: Displays results with colored output and summary statistics

## Safety Features

- **Non-Destructive**: Never modifies uncommitted changes
- **Skip Dirty Repos**: Automatically skips repositories with uncommitted changes
- **Error Resilience**: Continues processing even if individual repositories fail
- **Clear Feedback**: Shows exactly what's happening with each repository

## Troubleshooting

### Git not found
Ensure Git is installed and available in your PATH.

### Permission errors
Some directories may not be accessible. Gitty Up will skip them and continue.

### Authentication failures
Repositories requiring authentication will fail. Ensure your Git credentials are configured.

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

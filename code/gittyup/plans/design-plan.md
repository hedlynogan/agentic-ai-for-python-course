# Gitty Up - Comprehensive Design Plan

## Executive Summary

Gitty Up is a professional-grade CLI tool that automatically discovers and updates all Git repositories within a directory tree. It solves the common problem of forgetting to pull changes before starting work, which leads to merge conflicts.

---

## 1. Requirements & Features

### 1.1 Core Requirements (MVP)
- **Directory Traversal**: Recursively scan directories to find Git repositories (identify by `.git` folder)
- **Git Pull Execution**: Execute `git pull --all` on each discovered repository
- **Colored Output**: Use colorama to provide visual feedback (success/error/info states)
- **Progress Reporting**: Show users which repos are being updated
- **Error Resilience**: Continue processing remaining repos if one fails
- **Summary Report**: Display final statistics (repos found, updated, failed)

### 1.2 Enhanced Features (Professional Grade)
- **Dry Run Mode**: Preview what would be updated without making changes (`--dry-run`)
- **Parallel Processing**: Update multiple repos concurrently for speed (configurable workers)
- **Exclusion Patterns**: Skip certain directories (e.g., `node_modules`, `venv`, `.tox`)
- **Depth Limiting**: Control how deep to traverse (`--max-depth`)
- **Verbose/Quiet Modes**: Control output verbosity
- **Status Reporting**: Show repos with uncommitted changes or unpushed commits
- **Branch Information**: Display current branch for each repo
- **Stash Support**: Option to stash changes before pulling
- **Configuration File**: Support `.gittyup.yaml` for project-specific settings
- **Multiple Strategies**: Support different update strategies (pull, fetch, pull with rebase)

### 1.3 User Experience Priorities
- **Clear Visual Hierarchy**: Use colors and symbols to communicate status at a glance
- **Non-intrusive**: Don't interrupt workflow unless critical issues arise
- **Fast**: Leverage async operations for large directory trees
- **Informative**: Provide actionable feedback on failures
- **Safe**: Never lose user data; warn before destructive operations

---

## 2. Technical Architecture

### 2.1 Project Structure
```
gittyup/
├── gittyup/                    # Main package
│   ├── __init__.py
│   ├── __main__.py            # Entry point for `python -m gittyup`
│   ├── cli.py                 # CLI argument parsing and main command
│   ├── scanner.py             # Directory traversal and repo discovery
│   ├── git_operations.py     # Git command execution
│   ├── reporter.py            # Output formatting and reporting
│   ├── config.py              # Configuration management
│   ├── models.py              # Data classes (RepoStatus, ScanResult, etc.)
│   └── constants.py           # Constants (colors, defaults, patterns)
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── test_scanner.py
│   ├── test_git_operations.py
│   ├── test_reporter.py
│   ├── test_cli.py
│   └── fixtures/              # Test fixtures
├── plans/                     # Design documents
├── pyproject.toml            # Project metadata and build config
├── requirements.piptools     # Runtime dependencies
├── requirements-development.piptools  # Dev dependencies
├── pytest.ini                # Pytest configuration
├── ruff.toml                 # Ruff configuration
├── readme.md                 # User documentation
└── venv/                     # Virtual environment
```

### 2.2 Core Modules

#### `cli.py` - Command Line Interface
- **Responsibility**: Parse arguments, validate inputs, orchestrate execution
- **Key Functions**:
  - `main()` - Entry point
  - `create_parser()` - Build argument parser
  - `validate_args()` - Validate user inputs
- **Dependencies**: argparse, pathlib

#### `scanner.py` - Repository Discovery
- **Responsibility**: Walk directory tree and identify Git repositories
- **Key Functions**:
  - `scan_directory(path, max_depth, exclude_patterns)` - Main scanning logic
  - `is_git_repo(path)` - Check if directory is a Git repo
  - `should_exclude(path, patterns)` - Apply exclusion rules
- **Returns**: Generator of Path objects for each repository
- **Approach**: Use `pathlib.Path.rglob()` or manual recursive walk with depth control

#### `git_operations.py` - Git Command Execution
- **Responsibility**: Execute Git commands and parse results
- **Key Functions**:
  - `pull_repository(repo_path, strategy)` - Execute pull operation
  - `get_repo_status(repo_path)` - Get working tree status
  - `get_current_branch(repo_path)` - Determine active branch
  - `has_uncommitted_changes(repo_path)` - Check for dirty working tree
  - `stash_changes(repo_path)` - Stash uncommitted changes
- **Implementation**: Use subprocess for Git commands
- **Error Handling**: Capture stderr, parse error messages, return structured results

#### `reporter.py` - Output and Reporting
- **Responsibility**: Format and display information to user
- **Key Functions**:
  - `print_header()` - Display startup banner
  - `report_repo_processing(repo_path, status)` - Show individual repo updates
  - `report_summary(results)` - Display final statistics
  - `format_error(error)` - Format error messages
- **Output Styles**:
  - ✓ Green for success
  - ✗ Red for errors
  - ⚠ Yellow for warnings
  - ℹ Blue for info
  - Progress indicators for long operations

#### `config.py` - Configuration Management
- **Responsibility**: Load and merge configuration from files and CLI
- **Key Functions**:
  - `load_config(path)` - Read `.gittyup.yaml` if present
  - `merge_config(file_config, cli_args)` - Combine sources
  - `get_default_excludes()` - Return sensible defaults
- **Config Format**: YAML for readability
- **Priority**: CLI args > local config > global config > defaults

#### `models.py` - Data Structures
- **Purpose**: Define clean data structures using dataclasses
- **Key Classes**:
  - `RepoStatus` - Holds result of processing a single repo
  - `ScanConfig` - Configuration for scanning operation
  - `UpdateStrategy` - Enum for pull/fetch/rebase options
  - `SummaryStats` - Aggregated results

### 2.3 Technology Stack

#### Core Dependencies
- **Python 3.11+**: Modern Python features (match statements, improved typing)
- **colorama**: Cross-platform colored terminal output
- **pyyaml**: Configuration file parsing (optional)
- **pathlib**: Path operations (built-in)
- **asyncio**: Concurrent operations (built-in)
- **subprocess**: Git command execution (built-in)

#### Development Dependencies
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Code coverage
- **ruff**: Linting and formatting
- **mypy**: Static type checking
- **build**: Package building
- **twine**: PyPI publishing

---

## 3. CLI Design

### 3.1 Command Structure
```bash
gittyup [OPTIONS] [PATH]
```

### 3.2 Arguments
- **PATH** (positional, optional): Root directory to scan (default: current directory)

### 3.3 Options

#### Operation Modes
- `--dry-run, -n`: Show what would be done without making changes
- `--status, -s`: Show status only (no pull operations)

#### Filtering & Traversal
- `--max-depth DEPTH`: Maximum directory depth to traverse (default: unlimited)
- `--exclude PATTERN`: Exclude directories matching pattern (can be repeated)
- `--include PATTERN`: Only include directories matching pattern

#### Git Operation
- `--strategy {pull,fetch,rebase}`: Update strategy (default: pull)
- `--stash`: Stash changes before pulling, pop after
- `--all`: Pull all branches (equivalent to `git pull --all`)
- `--no-pull`: Skip pull operations (status only)

#### Output Control
- `--wordy, -w`: Increase output detail/verbosity (can be repeated: -ww, -www)
- `--quiet, -q`: Minimize output (errors only)
- `--no-color`: Disable colored output
- `--format {text,json}`: Output format (default: text)

#### Performance
- `--workers N`: Number of concurrent workers (default: 4)
- `--sequential`: Disable parallel processing

#### Configuration
- `--config FILE`: Use specific config file
- `--no-config`: Ignore config files

#### Help & Info
- `--help, -h`: Show help message
- `--version`: Show version information

### 3.4 Output Examples

#### Standard Operation
```
🚀 Gitty Up - Scanning /Users/dev/projects...
   Found 15 git repositories

Updating repositories...
✓ project-alpha (main) - Already up to date
✓ project-beta (develop) - Fast-forward: 3 commits
⚠ project-gamma (feature/new) - Uncommitted changes, skipped
✗ project-delta (main) - Error: Authentication failed

Summary:
  📊 Repositories found: 15
  ✓ Successfully updated: 12
  ⚠ Skipped: 1
  ✗ Failed: 1
  ⏱ Duration: 12.3s
```

#### Verbose Mode
```
🔍 Scanning directory: /Users/dev/projects
  Depth: unlimited
  Exclude patterns: ['node_modules', 'venv', '.venv', '.tox']
  Workers: 4

Found repositories:
  1. /Users/dev/projects/project-alpha
  2. /Users/dev/projects/project-beta
  ...

[project-alpha]
  Path: /Users/dev/projects/project-alpha
  Branch: main
  Status: Clean working tree
  Remote: origin
  Executing: git pull --all
  Output: Already up to date
  ✓ Success

...
```

---

## 4. Error Handling Strategy

### 4.1 Error Categories

#### 1. User Input Errors
- Invalid path provided
- Conflicting options
- **Handling**: Display clear error message and help hint, exit with code 1

#### 2. Permission Errors
- No read access to directory
- No write access to `.git` directory
- **Handling**: Show warning, skip directory, continue with others

#### 3. Git Errors
- Not a valid git repository
- Authentication required
- Network issues
- Merge conflicts detected
- Detached HEAD state
- **Handling**: Capture error, display formatted message, mark repo as failed, continue

#### 4. System Errors
- Git not installed
- Out of disk space
- Interrupt signal (Ctrl+C)
- **Handling**: Display helpful message with remediation steps

### 4.2 Error Recovery
- **Principle**: Never leave repositories in broken state
- **Approach**: Each operation is atomic and can be safely retried
- **Logging**: Option to write detailed logs for troubleshooting

### 4.3 Exit Codes
- `0` - Success (all repos updated)
- `1` - User error (invalid arguments)
- `2` - Partial failure (some repos failed)
- `3` - Complete failure (no repos updated)
- `130` - Interrupted by user (Ctrl+C)

---

## 5. Testing Strategy

### 5.1 Unit Tests
- **scanner.py**:
  - Test directory traversal
  - Test Git repo detection
  - Test exclusion patterns
  - Test depth limiting
- **git_operations.py**:
  - Mock subprocess calls
  - Test success paths
  - Test error handling
  - Test output parsing
- **reporter.py**:
  - Test output formatting
  - Test color codes
  - Test summary calculations
- **config.py**:
  - Test YAML parsing
  - Test config merging
  - Test default values

### 5.2 Integration Tests
- Create temporary Git repos
- Execute full scan and update cycle
- Verify correct behavior with:
  - Clean repos
  - Repos with uncommitted changes
  - Repos with unpushed commits
  - Nested repos
  - Non-Git directories mixed in

### 5.3 Edge Cases & Special Scenarios
- Empty directories
- Symbolic links (don't follow to avoid cycles)
- Very deep directory trees (>100 levels)
- Repos with submodules
- Bare repositories
- Corrupted `.git` directories
- Repos with detached HEAD
- Repos with merge conflicts
- Concurrent access by multiple gittyup instances

### 5.4 Performance Tests
- Large directory trees (1000+ repos)
- Measure parallel vs sequential performance
- Memory usage with many concurrent operations

### 5.5 Coverage Goals
- Minimum 85% code coverage
- 100% coverage for core logic (git operations, scanning)

---

## 6. Configuration System

### 6.1 Configuration File Format

#### `.gittyup.yaml` (project-level)
```yaml
# Directory scanning
max_depth: 3
exclude:
  - node_modules
  - venv
  - .venv
  - .tox
  - __pycache__
  - .pytest_cache

# Git operations
strategy: pull
stash_before_pull: false
pull_all_branches: true

# Performance
max_workers: 4

# Output
verbose: false
no_color: false
```

### 6.2 Configuration Precedence
1. Command-line arguments (highest priority)
2. `.gittyup.yaml` in current directory
3. `~/.config/gittyup/config.yaml` (user-level)
4. Built-in defaults (lowest priority)

### 6.3 Default Exclusions
```python
DEFAULT_EXCLUDES = [
    'node_modules',
    'venv',
    '.venv',
    'env',
    '.env',
    '.tox',
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    'dist',
    'build',
    '.eggs',
]
```

---

## 7. Performance Considerations

### 7.1 Optimization Strategies
- **Parallel Processing**: Use asyncio to pull multiple repos concurrently
  - Configurable worker pool (default: 4)
  - Respect system resources
- **Early Exclusion**: Skip excluded directories immediately during traversal
- **Lazy Loading**: Use generators to avoid loading all paths into memory
- **Smart Depth Control**: Stop descending when max depth reached

### 7.2 Resource Limits
- Limit concurrent subprocess (4-8 concurrent git pulls)
- Stream output rather than buffering for large directory trees
- Use `subprocess.run()` with timeout to prevent hanging

### 7.3 Progress Indication
- For operations >2 seconds, show progress indicator
- Update progress bar or spinner as repos are processed
- Show ETA for long operations

---

## 8. Security Considerations

### 8.1 Input Validation
- Sanitize path inputs
- Prevent path traversal attacks
- Validate configuration file contents

### 8.2 Safe Git Operations
- Never execute arbitrary commands
- Whitelist allowed git commands
- Don't follow symbolic links outside root directory

### 8.3 Credentials
- Never store or display credentials
- Rely on user's existing Git credential configuration
- Inform users about authentication failures without exposing sensitive data

---

## 9. Documentation Plan

### 9.1 User Documentation

#### README.md
- Quick start guide
- Installation instructions
- Common use cases with examples
- Troubleshooting section

#### CLI Help Text
- Comprehensive `--help` output
- Example commands for common scenarios

#### Online Documentation (Optional)
- Full feature documentation
- Configuration reference
- FAQ
- Best practices

### 9.2 Developer Documentation

#### Contributing Guide
- Code style guidelines
- How to run tests
- How to submit PRs

#### Architecture Documentation
- Module overview
- Key design decisions
- Extension points

#### API Documentation
- Docstrings for all public functions
- Type hints throughout

---

## 10. Distribution & Installation

### 10.1 Package Distribution
- **PyPI Package**: Publish to PyPI for easy installation
  - Package name: `gittyup`
  - Install: `pip install gittyup` or `uv pip install gittyup`
- **Entry Point**: Register console script in pyproject.toml
  ```toml
  [project.scripts]
  gittyup = "gittyup.cli:main"
  ```

### 10.2 Installation Methods

#### From PyPI (Primary)
```bash
uv pip install gittyup
# or
pip install gittyup
```

#### From Source (Development)
```bash
git clone <repo-url>
cd gittyup
uv pip install -e .
```

### 10.3 Version Management
- Semantic versioning (e.g., 1.0.0)
- Store version in `gittyup/__init__.py`
- Bump version for each release

---

## 11. Implementation Phases

### Phase 1: Core Functionality (MVP)
- **Goal**: Working CLI that scans and pulls repos
- **Tasks**:
  1. Project setup (structure, dependencies, config files)
  2. Implement basic scanner (find repos)
  3. Implement git operations (pull)
  4. Implement basic reporter (colored output)
  5. Implement CLI with basic options
  6. Basic tests
  7. README documentation

### Phase 2: Enhanced Features
- **Goal**: Professional-grade features
- **Tasks**:
  1. Add parallel processing
  2. Implement dry-run mode
  3. Add configuration file support
  4. Implement exclusion patterns
  5. Add status reporting
  6. Enhanced error handling
  7. Comprehensive tests

### Phase 3: Advanced Features
- **Goal**: Power user features
- **Tasks**:
  1. Multiple update strategies
  2. Stash support
  3. JSON output format
  4. Verbose/quiet modes
  5. Progress indicators
  6. Performance optimizations

### Phase 4: Polish & Distribution
- **Goal**: Ready for public release
- **Tasks**:
  1. Complete test coverage
  2. Full documentation
  3. PyPI packaging
  4. CI/CD setup
  5. Release automation

---

## 12. Success Criteria

### 12.1 Functional Requirements Met
- ✓ Correctly identifies all Git repositories in directory tree
- ✓ Successfully pulls updates from all remotes
- ✓ Handles errors gracefully without stopping
- ✓ Provides clear, colored output
- ✓ Completes operations in reasonable time

### 12.2 Quality Standards
- ✓ 85%+ test coverage
- ✓ No critical bugs
- ✓ All linter checks pass
- ✓ Type hints throughout
- ✓ Clear documentation

### 12.3 User Experience
- ✓ Intuitive CLI interface
- ✓ Helpful error messages
- ✓ Fast execution (parallel processing)
- ✓ Easy to install
- ✓ Works cross-platform (Windows, Mac, Linux)

---

## 13. Future Enhancements (Post-MVP)

### Potential Features to Consider Later
1. **Interactive Mode**: Prompt user before updating each repo
2. **Webhook Integration**: Notify external systems of updates
3. **Report Export**: Save results to file (JSON, CSV, HTML)
4. **Custom Commands**: Run arbitrary commands in each repo
5. **Branch Management**: Switch branches based on patterns
6. **Notification System**: Desktop notifications for completion
7. **Watch Mode**: Monitor directories and auto-pull on changes
8. **GitHub/GitLab Integration**: Use APIs for additional metadata
9. **Diff Summary**: Show high-level summary of changes pulled
10. **Rollback Support**: Undo last gittyup operation

---

## 14. Risk Assessment

### Technical Risks
1. **Git Command Variability**: Different Git versions may have different output formats
   - **Mitigation**: Test with multiple Git versions, use porcelain commands where available
2. **Performance with Large Trees**: Scanning thousands of repos may be slow
   - **Mitigation**: Async operations, progress feedback, configurable depth limits
3. **Merge Conflicts**: Pull may introduce conflicts
   - **Mitigation**: Detect conflicts, report them, don't attempt auto-resolution

### User Experience Risks
1. **Unexpected Behavior**: Users may not want all repos updated
   - **Mitigation**: Dry-run mode, clear documentation, exclusion patterns
2. **Data Loss Fear**: Users may worry about losing uncommitted work
   - **Mitigation**: Skip dirty repos by default, offer stash option, clear messaging

### Distribution Risks
1. **Platform Compatibility**: Behavior may differ on Windows vs Unix
   - **Mitigation**: Test on all platforms, use pathlib, handle line endings

---

## 15. Open Questions (To Resolve During Development)

1. Should we follow symlinks? (Recommendation: No, to avoid cycles)
2. What to do with submodules? (Recommendation: Update them with `--recurse-submodules`)
3. Should we support bare repositories? (Recommendation: Yes, but no working tree operations)
4. How to handle repositories with multiple remotes? (Recommendation: Pull from tracking branch's remote)
5. Should we create a log file by default? (Recommendation: Only in verbose mode or on error)

---

## 16. Development Timeline Estimate

**Phase 1 (MVP)**: 2-3 days
- Day 1: Project setup + scanner + git operations
- Day 2: CLI + reporter + basic testing
- Day 3: Integration testing + documentation

**Phase 2 (Enhanced)**: 2-3 days
- Parallel processing, config system, enhanced features

**Phase 3 (Advanced)**: 1-2 days
- Power user features, optimizations

**Phase 4 (Polish)**: 1-2 days
- Final testing, documentation, packaging

**Total Estimate**: 6-10 days for full implementation

---

## Summary

This plan provides a comprehensive roadmap for building Gitty Up as a professional-grade CLI tool. The design emphasizes:
- **Robustness**: Thorough error handling and testing
- **Performance**: Async operations for speed
- **Usability**: Clear output and intuitive interface
- **Flexibility**: Configuration and multiple operation modes
- **Quality**: High test coverage and documentation

The phased approach allows for incremental development with each phase delivering value, while building toward a polished, production-ready tool.


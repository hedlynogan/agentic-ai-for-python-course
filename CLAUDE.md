# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the course repository for "Agentic AI for Python" (training.talkpython.fm), which teaches developers how to effectively collaborate with agentic AI tools. The repository contains two main example projects demonstrating different application types and AI-assisted development techniques.

## Project Structure

The repository is organized into two independent example projects:

### 1. Gitty Up (`code/gittyup/`)
A production-grade CLI tool for batch updating Git repositories. This demonstrates:
- **Architecture**: Modular Python package with separate concerns (scanner, git operations, reporting, config)
- **Core modules**:
  - `cli.py` - Argument parsing and main entry point
  - `scanner.py` - Directory traversal and repository discovery
  - `git_operations.py` - Git command execution and error handling
  - `reporter.py` - Output formatting (text and JSON)
  - `config.py` - Configuration file management (.gittyup.yaml)
  - `models.py` - Data structures (RepoStatus, ScanConfig, SummaryStats, etc.)
  - `constants.py` - Default values and constants
- **Testing**: Comprehensive pytest suite with 59%+ coverage
- **Entry point**: Installed as `gittyup` command via pyproject.toml scripts section

### 2. Audio Player (`code/audio-player/`)
A vanilla JavaScript web application for podcast playback. This demonstrates:
- **Architecture**: Static HTML/CSS/JS with no build process
- **Stack**: HTML5 audio, Bulma CSS, vanilla JavaScript
- **Data**: JSON-based episode storage (tracks.json)
- **Files**: index.html (listing), details.html (player), styles.css, index.js, details.js

## Development Commands

### Virtual Environment
```bash
# The repository uses a .venv at the root level
# Activate before any Python work:
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

### Gitty Up Project (code/gittyup/)

**Run the application:**
```bash
cd code/gittyup
python -m gittyup ~/path/to/scan
# Or after installation:
gittyup ~/path/to/scan
```

**Install in development mode:**
```bash
cd code/gittyup
pip install -e .
```

**Run tests:**
```bash
cd code/gittyup
pytest                           # Run all tests
pytest tests/test_scanner.py     # Run specific test file
pytest --cov                     # Run with coverage report
pytest -v                        # Verbose output
```

**Linting and formatting:**
```bash
cd code/gittyup
ruff format .                    # Format all Python files
ruff check --fix .               # Fix linting issues
```

**Dependency management:**
```bash
cd code/gittyup
# Update runtime dependencies:
uv pip-compile requirements.piptools -o requirements.txt
uv pip install -r requirements.txt

# Update development dependencies:
uv pip-compile requirements-development.piptools -o requirements-dev.txt
uv pip install -r requirements-dev.txt
```

### Audio Player Project (code/audio-player/)

**Run the development server:**
```bash
cd code/audio-player
python -m http.server -b 127.0.0.1 10000
# Or with uv:
uv run python -m http.server -b 127.0.0.1 10000
# Then open http://127.0.0.1:10000/
```

**Note**: The server may already be running. Check before starting a new instance - it supports auto-reload for changes.

## Python Code Standards

### Technical Requirements
- **Python version**: 3.14+ (use latest syntax)
- **Path operations**: Use `pathlib.Path` (not `os.path`)
- **Async operations**: Use async/await pattern
- **Type hints**: Use builtin types (`list[int]` not `typing.List[int]`)
- **Optional types**: Use `Optional[type]` (not `type | None`)
- **No shebangs**: Don't use `#!/usr/bin/env python3` (run via venv or `uv run`)

### Code Style
- **Follow PEP8** and Ruff formatting guidelines (see ruff.toml in gittyup project)
- **Guard clauses**: Use early returns instead of nested conditionals
- **Keep functions small** and focused on single responsibilities
- **Prefer functions over classes** unless OOP truly fits the use case
- **Prefer modules over heavy inheritance**

### Import Style (Critical)
**Functions**: Use namespace imports
```python
# ✅ Correct
from gittyup import scanner
repos = scanner.scan_directory(path)

# ❌ Wrong
from gittyup.scanner import scan_directory
```

**Classes/Exceptions**: Use direct imports
```python
# ✅ Correct
from gittyup.models import RepoStatus, ScanConfig
status = RepoStatus(...)

# ❌ Wrong
from gittyup import models
status = models.RepoStatus(...)
```

### Error Handling
- Implement proper error handling for all external operations (file I/O, git commands, network)
- Use specific exception types rather than bare `except:`
- Provide meaningful error messages

## Configuration Files

### Dependencies
- **requirements.piptools**: Top-level runtime dependencies (input file)
- **requirements-development.piptools**: Development dependencies (input file)
- **requirements.txt**: Auto-generated lock file (via `uv pip-compile`)
- **pyproject.toml**: Package metadata and build configuration
- Keep pyproject.toml and *.piptools dependencies in sync

### Testing
- **pytest.ini**: Preferred location for pytest configuration (not pyproject.toml)
- Configuration includes coverage reporting, async support, and strict markers

### Linting/Formatting
- **ruff.toml**: Ruff configuration (in gittyup project)
- Enabled rules: pycodestyle, pyflakes, isort, pyupgrade, bugbear, simplify, mccabe
- Max complexity: 10
- Quote style: double quotes
- Run `ruff format` and `ruff check --fix` on all edited Python files

## Web Development Standards

- **CSS framework**: Use Bulma (preferred) or Bootstrap if already present
- **JavaScript**: Prefer vanilla JavaScript over frameworks
- **No inline styles/scripts**: Extract `<style>` and `<script>` blocks to separate .css and .js files
- **Web server ports**: Always use port 10000 or higher for development

## Git Workflow

- **Before starting work**: Run `git pull` at the beginning of each session
- **Before committing**: Run `ruff format` and `ruff check --fix` on Python files
- **Commit messages**: Concise summaries focused on "why" not "what"
- **Branching**: Main branch is `main`

## Custom Cursor Commands and Agents

### Slash Commands

**`/test-review`** (gittyup project only)
Acts as a quality engineer to review unit tests:
1. Verifies pytest is installed and configured
2. Checks pytest.ini optimization
3. Runs all tests and ensures they pass
4. Ensures no warnings in test output

**`/web-design-cleanup`** (audio-player project only)
Acts as a Web Design expert to ensure DRY principles:
1. Finds inline CSS in `<style>` blocks and moves to .css files
2. Finds inline JavaScript in `<script>` blocks and moves to .js files
3. Minimizes inline style attributes where appropriate

### Custom Agents

**@Brand Guardian** (defined in gittyup/AGENTS.md)
Expert brand strategist for brand identity and consistency. Use for:
- Brand strategy development (purpose, vision, mission, values)
- Visual identity systems (logos, colors, typography)
- Brand voice and messaging
- Brand protection and monitoring

## Tools and Utilities

- **Dependency management**: Use `uv` commands (`uv pip install`, `uv pip-compile`)
- **Testing**: pytest with coverage reporting
- **Linting**: ruff (replaces Black, flake8, isort)
- **Virtual env**: Created with `uv venv --python /opt/homebrew/bin/python3.14 .venv`

## Working with Specific Modules

### Gitty Up Architecture Notes

The application follows a clear separation of concerns:

1. **Scanner** discovers repositories by traversing directories and filtering excluded paths
2. **Git Operations** executes git commands with proper error handling and safety checks
3. **Reporter** formats output in either human-readable text or JSON for automation
4. **Config** manages .gittyup.yaml files with precedence: CLI args > local config > user config > defaults
5. **Models** define data structures used across modules (use dataclasses or TypedDicts)
6. **CLI** orchestrates everything and handles async execution with worker pools

**Key patterns**:
- Parallel processing with configurable workers (default: 4)
- Safety-first: never modifies repos with uncommitted changes (unless --stash)
- Smart exclusions: skips node_modules, venv, build dirs, etc.
- Multiple strategies: pull, fetch, or rebase

### Audio Player Architecture Notes

Simple client-side application with no backend:

- **Data flow**: Fetch tracks.json → render episode list → navigate to details → play audio
- **State management**: URL parameters for passing episode index between pages
- **Styling**: Bulma CSS classes for responsive design
- **Audio**: HTML5 `<audio>` element with native controls

## Course Context

This repository is for educational purposes, teaching developers how to:
- Guide agentic AI tools effectively
- Set up proper guardrails and conventions
- Build complete features autonomously with AI assistance
- Maintain code quality and consistency with AI collaboration

When working in this repository, demonstrate best practices for AI-assisted development.

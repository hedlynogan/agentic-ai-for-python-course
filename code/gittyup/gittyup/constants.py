"""Constants and default values for Gitty Up."""

from colorama import Fore, Style

# Color codes
COLOR_SUCCESS = Fore.GREEN
COLOR_ERROR = Fore.RED
COLOR_WARNING = Fore.YELLOW
COLOR_INFO = Fore.CYAN
COLOR_RESET = Style.RESET_ALL
COLOR_BOLD = Style.BRIGHT
COLOR_DIM = Style.DIM

# Symbols
SYMBOL_SUCCESS = "✓"
SYMBOL_ERROR = "✗"
SYMBOL_WARNING = "⚠"
SYMBOL_INFO = "ℹ"
SYMBOL_ROCKET = "🚀"
SYMBOL_STATS = "📊"
SYMBOL_CLOCK = "⏱"

# Default exclusion patterns
DEFAULT_EXCLUDES = [
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    ".tox",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".eggs",
    "target",  # Rust/Java
    "vendor",  # Go/PHP
]

# Git-related constants
GIT_DIR = ".git"
DEFAULT_MAX_WORKERS = 4
GIT_COMMAND_TIMEOUT = 60  # seconds

"""Configuration management for Gitty Up."""

from pathlib import Path
from typing import Any

import yaml

from gittyup import constants
from gittyup.models import UpdateStrategy


def load_config_file(config_path: Path) -> dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Dictionary of configuration values
    """
    if not config_path.exists():
        return {}

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except yaml.YAMLError:
        return {}
    except Exception:
        return {}


def get_config_paths() -> list[Path]:
    """
    Get list of configuration file paths in order of precedence.

    Returns:
        List of potential config file paths (highest to lowest priority)
    """
    paths = []

    # Local config (highest priority)
    local_config = Path.cwd() / ".gittyup.yaml"
    if local_config.exists():
        paths.append(local_config)

    # User config
    user_config_dir = Path.home() / ".config" / "gittyup"
    user_config = user_config_dir / "config.yaml"
    if user_config.exists():
        paths.append(user_config)

    return paths


def load_config() -> dict[str, Any]:
    """
    Load configuration from all available sources.

    Returns:
        Merged configuration dictionary with defaults
    """
    # Start with defaults
    config: dict[str, Any] = {
        "max_depth": None,
        "exclude": constants.DEFAULT_EXCLUDES.copy(),
        "strategy": "pull",
        "stash_before_pull": False,
        "pull_all_branches": True,
        "max_workers": constants.DEFAULT_MAX_WORKERS,
        "verbose": False,
        "no_color": False,
    }

    # Load and merge config files (reverse order - lowest priority first)
    for config_path in reversed(get_config_paths()):
        file_config = load_config_file(config_path)
        config.update(file_config)

    return config


def merge_config_with_args(
    config: dict[str, Any], args: dict[str, Any]
) -> dict[str, Any]:
    """
    Merge configuration from file with CLI arguments.

    CLI arguments take precedence over file configuration.

    Args:
        config: Configuration from file
        args: CLI arguments

    Returns:
        Merged configuration
    """
    result = config.copy()

    # CLI args override file config (only if explicitly provided)
    for key, value in args.items():
        if value is not None:
            result[key] = value

    return result


def parse_strategy(strategy_str: str) -> UpdateStrategy:
    """
    Parse update strategy from string.

    Args:
        strategy_str: Strategy string (pull, fetch, rebase)

    Returns:
        UpdateStrategy enum value
    """
    strategy_map = {
        "pull": UpdateStrategy.PULL,
        "fetch": UpdateStrategy.FETCH,
        "rebase": UpdateStrategy.REBASE,
    }
    return strategy_map.get(strategy_str.lower(), UpdateStrategy.PULL)

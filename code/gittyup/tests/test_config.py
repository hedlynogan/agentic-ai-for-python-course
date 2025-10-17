"""Tests for configuration management."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from gittyup import config
from gittyup.models import UpdateStrategy


def test_load_config_file_success(tmp_path: Path) -> None:
    """Test loading a valid configuration file."""
    config_data = {"max_depth": 3, "strategy": "pull", "max_workers": 8}
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    result = config.load_config_file(config_file)
    assert result == config_data


def test_load_config_file_not_exists() -> None:
    """Test loading a non-existent configuration file."""
    result = config.load_config_file(Path("/nonexistent/config.yaml"))
    assert result == {}


def test_load_config_file_invalid_yaml(tmp_path: Path) -> None:
    """Test loading an invalid YAML file."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("invalid: yaml: content: [[[")

    result = config.load_config_file(config_file)
    assert result == {}


def test_load_config_file_empty(tmp_path: Path) -> None:
    """Test loading an empty configuration file."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("")

    result = config.load_config_file(config_file)
    assert result == {}


def test_get_config_paths_local_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test getting config paths when local config exists."""
    monkeypatch.chdir(tmp_path)
    local_config = tmp_path / ".gittyup.yaml"
    local_config.touch()

    paths = config.get_config_paths()
    assert len(paths) >= 1
    assert paths[0] == local_config


def test_get_config_paths_user_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Test getting config paths when user config exists."""
    # Mock home directory
    user_config_dir = tmp_path / ".config" / "gittyup"
    user_config_dir.mkdir(parents=True)
    user_config = user_config_dir / "config.yaml"
    user_config.touch()

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    (tmp_path / "work").mkdir()
    monkeypatch.chdir(tmp_path / "work")

    paths = config.get_config_paths()
    assert user_config in paths


def test_load_config_with_defaults() -> None:
    """Test loading configuration with defaults."""
    with patch.object(config, "get_config_paths", return_value=[]):
        result = config.load_config()

    assert result["max_depth"] is None
    assert result["strategy"] == "pull"
    assert result["max_workers"] == 4
    assert result["verbose"] is False
    assert result["no_color"] is False
    assert "exclude" in result


def test_merge_config_with_args_cli_takes_precedence() -> None:
    """Test that CLI arguments take precedence over file config."""
    file_config = {"max_depth": 3, "strategy": "pull", "max_workers": 4}
    cli_args = {"max_depth": 5, "max_workers": 8}

    result = config.merge_config_with_args(file_config, cli_args)

    assert result["max_depth"] == 5  # CLI arg wins
    assert result["strategy"] == "pull"  # From file (not overridden)
    assert result["max_workers"] == 8  # CLI arg wins


def test_merge_config_with_args_none_values_ignored() -> None:
    """Test that None values in CLI args don't override file config."""
    file_config = {"max_depth": 3, "max_workers": 4}
    cli_args = {"max_depth": None, "max_workers": 8}

    result = config.merge_config_with_args(file_config, cli_args)

    assert result["max_depth"] == 3  # File config preserved
    assert result["max_workers"] == 8  # CLI arg applied


def test_parse_strategy_pull() -> None:
    """Test parsing pull strategy."""
    assert config.parse_strategy("pull") == UpdateStrategy.PULL
    assert config.parse_strategy("PULL") == UpdateStrategy.PULL


def test_parse_strategy_fetch() -> None:
    """Test parsing fetch strategy."""
    assert config.parse_strategy("fetch") == UpdateStrategy.FETCH
    assert config.parse_strategy("FETCH") == UpdateStrategy.FETCH


def test_parse_strategy_rebase() -> None:
    """Test parsing rebase strategy."""
    assert config.parse_strategy("rebase") == UpdateStrategy.REBASE
    assert config.parse_strategy("REBASE") == UpdateStrategy.REBASE


def test_parse_strategy_invalid() -> None:
    """Test parsing invalid strategy returns default."""
    assert config.parse_strategy("invalid") == UpdateStrategy.PULL

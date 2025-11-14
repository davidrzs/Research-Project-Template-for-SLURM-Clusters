"""Utilities for loading and validating configuration files."""

from pathlib import Path
from typing import Any

from omegaconf import OmegaConf


def load_config(config_path: str | Path) -> Any:
    """Load YAML configuration file using OmegaConf.

    Args:
        config_path: Path to YAML config file

    Returns:
        OmegaConf configuration object

    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    config = OmegaConf.load(config_path)
    return config


def save_config(config: Any, output_path: str | Path) -> None:
    """Save configuration to YAML file.

    Args:
        config: OmegaConf configuration object
        output_path: Path to save YAML file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        OmegaConf.save(config, f)


def merge_configs(*configs: Any) -> Any:
    """Merge multiple configuration objects.

    Later configs override earlier ones.

    Args:
        *configs: Variable number of OmegaConf objects to merge

    Returns:
        Merged OmegaConf configuration
    """
    return OmegaConf.merge(*configs)

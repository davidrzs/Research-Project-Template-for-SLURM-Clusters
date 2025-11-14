"""Utilities for setting up logging and experiment tracking."""

import logging
import sys
from pathlib import Path
from typing import Optional

import wandb


def setup_logging(
    output_dir: Optional[Path] = None,
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """Setup logging with file and console handlers.

    Args:
        output_dir: Directory to save log file (experiment.log)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("experiment")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Add console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add file handler
    if log_to_file and output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(output_dir / "experiment.log")
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def init_wandb(
    project: str,
    name: Optional[str] = None,
    config: Optional[dict] = None,
    tags: Optional[list] = None,
    notes: Optional[str] = None,
    dir: Optional[Path] = None,
    mode: str = "online",
) -> wandb.run:
    """Initialize Weights & Biases experiment tracking.

    Args:
        project: W&B project name
        name: Run name (optional, auto-generated if not provided)
        config: Configuration dictionary to log
        tags: List of tags for this run
        notes: Optional notes about this run
        dir: Directory to save W&B files
        mode: W&B mode ("online", "offline", or "disabled")

    Returns:
        W&B run object
    """
    run = wandb.init(
        project=project,
        name=name,
        config=config,
        tags=tags,
        notes=notes,
        dir=str(dir) if dir else None,
        mode=mode,
    )
    return run


def finish_wandb():
    """Finish W&B run."""
    wandb.finish()

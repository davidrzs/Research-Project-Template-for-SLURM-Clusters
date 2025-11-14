"""Utilities for generating experiment metadata."""

import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


def generate_timestamp() -> str:
    """Generate timestamp in format YYYY-MM-DD_HH-MM-SS.

    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def generate_uuid(length: int = 8) -> str:
    """Generate short UUID for unique experiment identification.

    Args:
        length: Number of characters from UUID to use (default: 8)

    Returns:
        Short UUID string
    """
    return str(uuid.uuid4())[:length]


def get_git_info() -> dict:
    """Get current git repository information.

    Returns:
        Dictionary with git hash, branch, and clean status.
        Returns empty strings if not in a git repository.
    """
    try:
        # Get current commit hash
        git_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()

        # Get current branch
        git_branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()

        # Check if working directory is clean
        git_status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        is_clean = len(git_status) == 0

        return {
            "hash": git_hash,
            "branch": git_branch,
            "is_clean": is_clean,
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git repository or git not available
        return {
            "hash": "",
            "branch": "",
            "is_clean": True,
        }


def save_metadata(
    output_dir: Path,
    config_path: str,
    job_id: Optional[str] = None,
    additional_metadata: Optional[dict] = None,
) -> None:
    """Save experiment metadata to JSON file.

    Args:
        output_dir: Directory to save metadata.json
        config_path: Path to the config file used
        job_id: SLURM job ID (if submitted)
        additional_metadata: Any additional metadata to include
    """
    git_info = get_git_info()

    metadata = {
        "timestamp": datetime.now().isoformat(),
        "config_path": config_path,
        "git": git_info,
    }

    if job_id:
        metadata["slurm_job_id"] = job_id

    if additional_metadata:
        metadata.update(additional_metadata)

    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

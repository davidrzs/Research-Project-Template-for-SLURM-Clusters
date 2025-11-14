#!/usr/bin/env python3
"""Submit multiple experiments to SLURM in batch.

This script allows you to submit multiple configuration files at once,
useful for parameter sweeps and running multiple experiments.

Examples:
    # Submit all sweep configs
    python batch_submit.py configs/sweep_*.yaml

    # Submit specific configs
    python batch_submit.py configs/exp1.yaml configs/exp2.yaml configs/exp3.yaml

    # Dry-run first
    python batch_submit.py --dry-run configs/sweep_*.yaml

    # Submit with delay between jobs
    python batch_submit.py --delay 2 configs/*.yaml
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Submit multiple experiments to SLURM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s configs/sweep_*.yaml
  %(prog)s configs/exp1.yaml configs/exp2.yaml
  %(prog)s --dry-run configs/*.yaml
  %(prog)s --delay 2 configs/sweep_*.yaml
        """,
    )

    parser.add_argument(
        "configs",
        type=str,
        nargs="+",
        help="Config files to submit (supports wildcards via shell expansion)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be submitted without actually submitting",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0,
        help="Delay in seconds between submissions (default: 0)",
    )

    # Pass-through arguments for submit.py
    parser.add_argument("--time", type=str, help="Override SLURM time limit")
    parser.add_argument("--mem-per-cpu", type=str, help="Override memory per CPU")
    parser.add_argument("--cpus-per-task", type=int, help="Override number of CPUs")
    parser.add_argument("--gpus", type=str, help="Override GPU request")
    parser.add_argument("--partition", type=str, help="Override SLURM partition")
    parser.add_argument("--output-base", type=str, help="Base directory for outputs")

    return parser.parse_args()


def build_submit_command(config_path: str, args) -> list[str]:
    """Build submit.py command for a config file.

    Args:
        config_path: Path to config file
        args: Parsed command line arguments

    Returns:
        List of command arguments
    """
    cmd = ["python", "submit.py", "--config", config_path]

    if args.dry_run:
        cmd.append("--dry-run")
    if args.time:
        cmd.extend(["--time", args.time])
    if args.mem_per_cpu:
        cmd.extend(["--mem-per-cpu", args.mem_per_cpu])
    if args.cpus_per_task:
        cmd.extend(["--cpus-per-task", str(args.cpus_per_task)])
    if args.gpus:
        cmd.extend(["--gpus", args.gpus])
    if args.partition:
        cmd.extend(["--partition", args.partition])
    if args.output_base:
        cmd.extend(["--output-base", args.output_base])

    return cmd


def main():
    args = parse_args()

    # Resolve config paths
    config_paths = []
    for pattern in args.configs:
        path = Path(pattern)
        if path.exists():
            config_paths.append(str(path))
        else:
            # Try expanding wildcards
            expanded = list(Path(".").glob(pattern))
            if expanded:
                config_paths.extend([str(p) for p in expanded])
            else:
                print(f"Warning: No files match pattern: {pattern}", file=sys.stderr)

    if not config_paths:
        print("Error: No config files found", file=sys.stderr)
        sys.exit(1)

    # Remove duplicates while preserving order
    config_paths = list(dict.fromkeys(config_paths))

    # Filter for YAML files
    config_paths = [p for p in config_paths if p.endswith((".yaml", ".yml"))]

    if not config_paths:
        print("Error: No YAML config files found", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(config_paths)} config file(s) to submit:")
    for i, config in enumerate(config_paths, 1):
        print(f"  {i}. {config}")
    print()

    if args.dry_run:
        print("DRY RUN MODE - No jobs will be submitted\n")

    # Track submission results
    submitted = []
    failed = []

    # Submit each config
    for i, config_path in enumerate(config_paths, 1):
        print(f"[{i}/{len(config_paths)}] Submitting {config_path}...")

        # Build and run submit command
        cmd = build_submit_command(config_path, args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=False,
                text=True,
            )

            if result.returncode == 0:
                submitted.append(config_path)
                print(f"✓ Success\n")
            else:
                failed.append(config_path)
                print(f"✗ Failed (exit code: {result.returncode})\n", file=sys.stderr)

        except Exception as e:
            failed.append(config_path)
            print(f"✗ Error: {e}\n", file=sys.stderr)

        # Delay between submissions (except after last one)
        if args.delay > 0 and i < len(config_paths):
            print(f"Waiting {args.delay}s before next submission...\n")
            time.sleep(args.delay)

    # Print summary
    print("=" * 70)
    print("BATCH SUBMISSION SUMMARY")
    print("=" * 70)
    print(f"Total configs: {len(config_paths)}")
    print(f"Successfully submitted: {len(submitted)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("\nFailed configs:")
        for config in failed:
            print(f"  - {config}")
        sys.exit(1)
    else:
        if not args.dry_run:
            print("\nAll jobs submitted successfully!")
            print("\nMonitor with:")
            print("  squeue -u $USER")
        else:
            print("\nDry-run complete. Use without --dry-run to submit.")


if __name__ == "__main__":
    main()

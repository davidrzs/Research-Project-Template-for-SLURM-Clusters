#!/usr/bin/env python3
"""Submit experiments to SLURM with automatic output directory management.

This script:
1. Loads experiment configuration from YAML
2. Creates timestamped output directory
3. Generates executable submit.sh script
4. Submits job to SLURM or shows dry-run
5. Saves metadata for reproducibility
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from src.utils import (
    load_config,
    save_config,
    save_metadata,
    generate_timestamp,
    generate_uuid,
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Submit experiment to SLURM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to experiment config YAML file",
    )

    # SLURM parameter overrides
    parser.add_argument("--time", type=str, help="Override SLURM time limit (e.g., 04:00:00)")
    parser.add_argument("--mem-per-cpu", type=str, help="Override memory per CPU (e.g., 4G)")
    parser.add_argument("--cpus-per-task", type=int, help="Override number of CPUs")
    parser.add_argument("--gpus", type=str, help="Override GPU request (e.g., rtx_3090:1)")
    parser.add_argument("--partition", type=str, help="Override SLURM partition")

    # Other options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be submitted without actually submitting",
    )
    parser.add_argument(
        "--output-base",
        type=str,
        default="outputs",
        help="Base directory for outputs (default: outputs)",
    )

    return parser.parse_args()


def get_slurm_params(config, args):
    """Extract SLURM parameters from config with CLI overrides.

    Args:
        config: Loaded configuration object
        args: Parsed command line arguments

    Returns:
        Dictionary of SLURM parameters
    """
    # Start with config defaults
    slurm = {}
    if hasattr(config, "slurm"):
        slurm = dict(config.slurm)

    # Apply CLI overrides
    if args.time:
        slurm["time"] = args.time
    if args.mem_per_cpu:
        slurm["mem_per_cpu"] = args.mem_per_cpu
    if args.cpus_per_task:
        slurm["cpus_per_task"] = args.cpus_per_task
    if args.gpus:
        slurm["gpus"] = args.gpus
    if args.partition:
        slurm["partition"] = args.partition

    # Set defaults if not specified
    slurm.setdefault("job_name", "experiment")
    slurm.setdefault("time", "04:00:00")
    slurm.setdefault("mem_per_cpu", "4G")
    slurm.setdefault("cpus_per_task", 1)

    return slurm


def generate_submit_script(
    script_path: str,
    config_path: str,
    output_dir: Path,
    slurm_params: dict,
) -> str:
    """Generate SLURM submit.sh script content.

    Args:
        script_path: Path to the Python script to run
        config_path: Path to the config file
        output_dir: Output directory path
        slurm_params: Dictionary of SLURM parameters

    Returns:
        Content of submit.sh script as string
    """
    # Build SBATCH directives
    sbatch_lines = [
        "#!/bin/bash",
        "",
        f"#SBATCH --job-name={slurm_params['job_name']}",
        f"#SBATCH --time={slurm_params['time']}",
        f"#SBATCH --mem-per-cpu={slurm_params['mem_per_cpu']}",
        f"#SBATCH --cpus-per-task={slurm_params['cpus_per_task']}",
    ]

    # Add GPU if requested
    if slurm_params.get("gpus"):
        sbatch_lines.append(f"#SBATCH --gpus={slurm_params['gpus']}")

    # Add partition if specified
    if slurm_params.get("partition"):
        sbatch_lines.append(f"#SBATCH --partition={slurm_params['partition']}")

    # Redirect output and error to output directory
    sbatch_lines.extend([
        f"#SBATCH --output={output_dir}/slurm-%j.out",
        f"#SBATCH --error={output_dir}/slurm-%j.err",
        "",
    ])

    # Add script content
    script_lines = [
        "# Print job information",
        'echo "Job ID: $SLURM_JOB_ID"',
        f'echo "Output directory: {output_dir}"',
        f'echo "Config: {config_path}"',
        'echo "Node: $SLURM_NODELIST"',
        'echo "Start time: $(date)"',
        "",
        "# Source environment setup",
        "source load-env.sh",
        "",
        "# Run experiment",
        f'uv run --env-file .env {script_path} \\',
        f'  --config {config_path} \\',
        f'  --output-dir {output_dir}',
        "",
        "# Capture exit code",
        "EXIT_CODE=$?",
        "",
        "# Write status",
        'if [ $EXIT_CODE -eq 0 ]; then',
        f'  echo "SUCCESS" > {output_dir}/status.txt',
        'else',
        f'  echo "FAILED (exit code: $EXIT_CODE)" > {output_dir}/status.txt',
        'fi',
        "",
        'echo "End time: $(date)"',
        'echo "Exit code: $EXIT_CODE"',
        "",
        "exit $EXIT_CODE",
    ]

    return "\n".join(sbatch_lines + script_lines)


def main():
    args = parse_args()

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)

    # Check that config has script field
    if not hasattr(config, "script"):
        print("Error: Config must have 'script' field", file=sys.stderr)
        sys.exit(1)

    script_path = config.script

    # Get SLURM parameters
    slurm_params = get_slurm_params(config, args)

    # Generate output directory name
    config_name = config_path.stem  # Filename without extension
    timestamp = generate_timestamp()
    unique_id = generate_uuid()
    output_dir_name = f"{config_name}_{timestamp}_{unique_id}"
    output_dir = Path(args.output_base) / output_dir_name

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save copy of config to output directory
    config_copy = output_dir / "config.yaml"
    save_config(config, config_copy)

    # Generate submit.sh script
    submit_script = generate_submit_script(
        script_path=script_path,
        config_path=str(config_path),
        output_dir=output_dir,
        slurm_params=slurm_params,
    )

    # Save submit.sh to output directory
    submit_sh_path = output_dir / "submit.sh"
    with open(submit_sh_path, "w") as f:
        f.write(submit_script)
    submit_sh_path.chmod(0o755)  # Make executable

    # Print information
    print(f"Experiment: {config_name}")
    print(f"Output directory: {output_dir}")
    print(f"Config: {config_path}")
    print(f"Script: {script_path}")
    print(f"\nSLurM parameters:")
    for key, value in slurm_params.items():
        print(f"  {key}: {value}")

    # Dry run or submit
    if args.dry_run:
        print("\n" + "=" * 70)
        print("DRY RUN - Generated submit.sh:")
        print("=" * 70)
        print(submit_script)
        print("=" * 70)
        print(f"\nSubmit script saved to: {submit_sh_path}")
        print("To submit manually, run:")
        print(f"  sbatch {submit_sh_path}")
    else:
        # Submit job
        print(f"\nSubmitting job...")
        result = subprocess.run(
            ["sbatch", str(submit_sh_path)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            # Parse job ID from sbatch output
            # Typical output: "Submitted batch job 12345"
            job_id = result.stdout.strip().split()[-1]
            print(f"Job submitted successfully!")
            print(f"Job ID: {job_id}")

            # Save metadata with job ID
            save_metadata(
                output_dir=output_dir,
                config_path=str(config_path),
                job_id=job_id,
            )

            print(f"\nMonitor job with:")
            print(f"  squeue -j {job_id}")
            print(f"  tail -f {output_dir}/slurm-{job_id}.out")
        else:
            print(f"Error submitting job:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()

"""Hello World example experiment.

This script demonstrates:
- Loading configuration with OmegaConf
- Setting up logging (file + console)
- Integrating with Weights & Biases
- Saving results to output directory
"""

import argparse
import random
import sys
from pathlib import Path

import numpy as np

from utils import load_config, setup_logging, init_wandb, finish_wandb


def set_seed(seed: int):
    """Set all random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Hello World experiment")
    parser.add_argument("--config", type=str, required=True, help="Path to config file")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory")
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logger = setup_logging(
        output_dir=output_dir,
        log_level="INFO",
        log_to_file=True,
        log_to_console=True,
    )

    logger.info("Starting Hello World experiment")
    logger.info(f"Config: {config}")
    logger.info(f"Output directory: {output_dir}")

    # Set seed for reproducibility
    if hasattr(config, "seed"):
        set_seed(config.seed)
        logger.info(f"Set seed to {config.seed}")

    # Initialize Weights & Biases (if enabled)
    wandb_run = None
    if hasattr(config, "wandb") and config.wandb.enabled:
        logger.info("Initializing Weights & Biases")
        wandb_run = init_wandb(
            project=config.wandb.project,
            name=config.wandb.get("name", None),
            config=dict(config),
            dir=output_dir,
            mode="online" if config.wandb.enabled else "disabled",
        )
        logger.info(f"W&B run: {wandb_run.name}")

    # Run experiment
    logger.info("Running experiment...")

    # Example: Generate some random data
    data = np.random.randn(100, 10)
    mean = data.mean()
    std = data.std()

    logger.info(f"Generated data shape: {data.shape}")
    logger.info(f"Mean: {mean:.4f}, Std: {std:.4f}")

    # Log metrics to W&B
    if wandb_run:
        wandb_run.log({"mean": mean, "std": std})

    # Save results
    results_file = output_dir / "results.txt"
    with open(results_file, "w") as f:
        f.write(f"Mean: {mean:.4f}\n")
        f.write(f"Std: {std:.4f}\n")

    logger.info(f"Results saved to {results_file}")

    # Save data
    data_file = output_dir / "data.npy"
    np.save(data_file, data)
    logger.info(f"Data saved to {data_file}")

    # Finish W&B run
    if wandb_run:
        finish_wandb()

    logger.info("Experiment completed successfully!")

    # Write success status
    status_file = output_dir / "status.txt"
    with open(status_file, "w") as f:
        f.write("SUCCESS\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Log error and write failure status
        import logging
        import traceback

        logger = logging.getLogger("experiment")
        logger.error(f"Experiment failed: {e}")
        logger.error(traceback.format_exc())

        # Try to write failure status
        try:
            import sys
            output_dir = None
            for i, arg in enumerate(sys.argv):
                if arg == "--output-dir" and i + 1 < len(sys.argv):
                    output_dir = Path(sys.argv[i + 1])
                    break

            if output_dir:
                status_file = output_dir / "status.txt"
                with open(status_file, "w") as f:
                    f.write(f"FAILED (exit code: 1)\n")
                    f.write(f"Error: {e}\n")
        except:
            pass

        sys.exit(1)

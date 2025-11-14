# ML Experiment Template for SLURM Clusters

Template repository for running machine learning experiments on SLURM-based HPC clusters. Designed for reproducible research with automatic experiment tracking, logging, and job management.

**Created by David Zollikofer with the help of Claude Code**

> Originally developed for ETH Zurich's Euler cluster, but works on any SLURM cluster with minimal configuration.

## Features

- Python-based SLURM job submission with automatic output directory management
- Configuration-driven experiments using YAML
- Integrated logging (file + console) and Weights & Biases tracking
- Reproducibility through git metadata and config snapshots
- Timestamped output directories with unique IDs
- Generated submit.sh scripts for re-running experiments

## Directory Structure

```
template/
├── configs/              # Experiment configuration files (YAML)
├── src/                  # Source code
│   ├── utils/           # Utility functions (logging, config, metadata)
│   └── *.py             # Experiment scripts
├── outputs/             # Auto-generated experiment outputs (gitignored)
├── data/                # Raw data files
├── submit.py            # Python script for SLURM submission
├── batch_submit.py      # Submit multiple configs at once
├── load-env.sh          # Environment setup (modules, cache paths)
├── pyproject.toml       # Python dependencies (managed by uv)
├── .env                 # API keys (create from .env.example)
├── CLAUDE.md            # Guide for Claude Code
└── README.md            # This file
```

## Quick Start

### 1. Setup

```bash
# Clone/copy this template to your project directory
cd your-project

# Create .env file from template
cp .env.example .env
# Edit .env and add your API keys (HF_TOKEN, WANDB_API_KEY)

# Install dependencies with uv
uv sync

# (Optional) Customize load-env.sh with required modules
```

### 2. Run Hello World Example

```bash
# Test with dry-run first
python submit.py --config configs/hello_world.yaml --dry-run

# Submit to SLURM
python submit.py --config configs/hello_world.yaml
```

### 3. Monitor Job

```bash
# Check job status
squeue -u $USER

# View output in real-time
tail -f outputs/hello_world_*/slurm-*.out

# Check results
ls outputs/hello_world_*/
```

## Cluster-Specific Configuration

### ETH Zurich Euler Cluster

This section contains Euler-specific configuration. If using a different SLURM cluster, adjust GPU types, modules, and storage paths accordingly.

#### Available GPU Types

Euler provides several GPU types for different workloads:

| GPU Type | SLURM Name | Memory | Best For | Example Config |
|----------|------------|--------|----------|----------------|
| NVIDIA A100 | `nvidia_a100_80gb:1` | 80GB | Large models, training | `gpus: "nvidia_a100_80gb:1"` |
| NVIDIA V100 | `nvidia_v100_32gb:1` | 32GB | Medium models | `gpus: "nvidia_v100_32gb:1"` |
| NVIDIA GeForce RTX | `nvidia_geforce_rtx_3090:1` | 24GB | Inference, fine-tuning | `gpus: "nvidia_geforce_rtx_3090:1"` |
| NVIDIA Titan RTX | `nvidia_geforce_rtx_titan_rtx:1` | 24GB | General purpose | `gpus: "nvidia_geforce_rtx_titan_rtx:1"` |

**Note**: GPU names may vary. Check current availability with:
```bash
sinfo -o "%40N %15G" | grep gpu
```

**Requesting multiple GPUs**:
```yaml
slurm:
  gpus: "nvidia_a100_80gb:2"  # Request 2 A100 GPUs
```

#### Modules to Load

Edit `load-env.sh` and uncomment the modules you need:

```bash
# For GPU workloads (CUDA support):
module load stack/2024-06 python_cuda/3.11.6

# For external network access (Hugging Face, wandb):
module load eth_proxy

# For development (VSCode server):
module load code-server
```

Check available modules:
```bash
module avail
module spider python
```

#### Storage and Quotas

- **Home directory** (`$HOME`): 50GB limit, backed up
  - Use for code, configs, small files
- **Scratch directory** (`$SCRATCH`): 2.5TB limit, NOT backed up
  - Use for models, datasets, caches, experiment outputs
  - Files deleted after 15 days of inactivity

**Important**: This template redirects all caches to `$SCRATCH` via `load-env.sh`:
```bash
export HF_HOME="$SCRATCH/.cache/huggingface"
export TORCH_HOME="$SCRATCH/.cache/torch"
export WANDB_CACHE_DIR="$SCRATCH/.cache/wandb"
```

#### Time Limits and Partitions

Jobs are automatically assigned to partitions based on requested time:

| Time Requested | Partition | Max Time | Typical Use |
|----------------|-----------|----------|-------------|
| < 4h | `*.4h` | 4 hours | Quick experiments, debugging |
| 4h - 24h | `*.24h` | 24 hours | Standard training |
| > 24h | `*.120h` | 120 hours | Long training runs |

Specify time in config:
```yaml
slurm:
  time: "04:00:00"  # 4 hours (HH:MM:SS)
  time: "1-12:00:00"  # 1 day, 12 hours (DD-HH:MM:SS)
```

#### Memory Guidelines

Rule of thumb for memory per CPU:

- **Light compute**: 4-8GB per CPU
- **Standard ML**: 8-16GB per CPU
- **Large models**: 16-32GB per CPU
- **Very large/data-intensive**: 32-64GB per CPU

```yaml
slurm:
  mem_per_cpu: "16G"  # 16GB per CPU
  cpus_per_task: 4     # Total: 64GB
```

#### Proxy for External Access

If downloading models/data or using wandb, load the proxy module:

```bash
# In load-env.sh or before running
module load eth_proxy
```

Without the proxy, external downloads will fail.

#### Checking Cluster Status

```bash
# Check GPU availability
sinfo -p gpu.4h -o "%20P %5a %10l %6D %6t %20N %20G"

# Your job queue
squeue -u $USER

# Cluster load
squeue -p gpu.4h

# Your storage quota
lquota
```

## Creating Your Own Experiments

### 1. Create a Config File

```yaml
# configs/my_experiment.yaml
script: src/my_experiment.py

slurm:
  job_name: my_experiment
  time: "04:00:00"
  mem_per_cpu: "8G"
  cpus_per_task: 4
  gpus: "rtx_3090:1"  # or null for CPU-only

# Your experiment parameters
seed: 42
model:
  name: "gpt2"
  batch_size: 32

wandb:
  enabled: true
  project: "my-project"
```

### 2. Create Experiment Script

```python
# src/my_experiment.py
import argparse
from pathlib import Path
from utils import load_config, setup_logging, init_wandb

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    output_dir = Path(args.output_dir)

    logger = setup_logging(output_dir=output_dir)
    logger.info("Starting experiment...")

    # Your experiment code here

    # Save results to output_dir

if __name__ == "__main__":
    main()
```

### 3. Submit to SLURM

```bash
# Basic submission
python submit.py --config configs/my_experiment.yaml

# Override SLURM parameters
python submit.py --config configs/my_experiment.yaml \
  --time 8:00:00 \
  --mem-per-cpu 16G \
  --gpus a100:1

# Dry-run to check before submitting
python submit.py --config configs/my_experiment.yaml --dry-run
```

## Output Directory Structure

Each experiment creates a unique output directory:

```
outputs/my_experiment_2025-11-14_14-30-22_a1b2c3d4/
├── submit.sh             # Generated SLURM script (executable)
├── config.yaml           # Copy of config used
├── metadata.json         # Git info, timestamp, job ID
├── slurm-12345.out       # SLURM stdout
├── slurm-12345.err       # SLURM stderr
├── experiment.log        # Application logs
├── status.txt            # SUCCESS or FAILED
└── [your results]        # Model outputs, plots, etc.
```

## Environment Setup (load-env.sh)

The `load-env.sh` script handles:

1. Loading required modules (Python, CUDA, etc.)
2. Redirecting cache directories to `$SCRATCH` (avoids home quota limits)
3. Loading API keys from `.env` file

**Important**: Edit `load-env.sh` to uncomment the modules you need:

```bash
# Load Python with CUDA support
module load stack/2024-06 python_cuda/3.11.6

# Load proxy for external network access
module load eth_proxy
```

## Utility Functions

### Config Loading

```python
from utils import load_config, save_config

config = load_config("configs/my_config.yaml")
save_config(config, output_dir / "config_copy.yaml")
```

### Logging

```python
from utils import setup_logging

logger = setup_logging(
    output_dir=output_dir,
    log_level="INFO",
    log_to_file=True,
    log_to_console=True
)

logger.info("This goes to both file and console")
```

### Weights & Biases

```python
from utils import init_wandb, finish_wandb

run = init_wandb(
    project="my-project",
    name="experiment-1",
    config=dict(config),
    dir=output_dir
)

run.log({"loss": 0.5, "accuracy": 0.95})
finish_wandb()
```

### Metadata

```python
from utils import get_git_info, save_metadata, generate_timestamp

git_info = get_git_info()  # Returns git hash, branch, clean status
timestamp = generate_timestamp()  # Returns YYYY-MM-DD_HH-MM-SS
```

## SLURM Tips

### Check Job Status

```bash
# Your jobs
squeue -u $USER

# Specific job
squeue -j JOB_ID

# Cancel job
scancel JOB_ID
```

### Monitor Output

```bash
# Real-time output
tail -f outputs/experiment_*/slurm-*.out

# Check errors
tail -f outputs/experiment_*/slurm-*.err
```

### Re-run Experiment

Each output directory contains a `submit.sh` that can be re-run:

```bash
# Submit the exact same job again
sbatch outputs/my_experiment_2025-11-14_14-30-22_a1b2c3d4/submit.sh
```

## Parameter Sweeps

For parameter sweeps, create multiple config files and use `batch_submit.py`:

```bash
# Create configs
for lr in 0.001 0.01 0.1; do
  cat > configs/sweep_lr_${lr}.yaml <<EOF
script: src/my_experiment.py
slurm:
  job_name: sweep_lr_${lr}
  time: "02:00:00"
learning_rate: ${lr}
EOF
done

# Submit all with batch_submit.py (recommended)
python batch_submit.py configs/sweep_*.yaml

# Or with delay between submissions
python batch_submit.py --delay 2 configs/sweep_*.yaml

# Dry-run first to check
python batch_submit.py --dry-run configs/sweep_*.yaml

# Alternative: Submit one-by-one manually
for config in configs/sweep_*.yaml; do
  python submit.py --config $config
done
```

## Best Practices

1. **Always use `--dry-run` first** to verify your submission
2. **Set seed in configs** for reproducibility
3. **Check git status** before running experiments (metadata tracks dirty repos)
4. **Use descriptive config names** (they become output directory names)
5. **Monitor first run** to ensure it works before parameter sweeps
6. **Save configs to outputs** (done automatically) for reproducibility

## Troubleshooting

### Job fails immediately

Check `slurm-*.err` in the output directory and verify:
- Modules are loaded correctly in `load-env.sh`
- API keys are set in `.env`
- Dependencies are installed (`uv sync`)

### Cache directory quota exceeded

Make sure `load-env.sh` redirects caches to `$SCRATCH`:

```bash
export HF_HOME="$SCRATCH/.cache/huggingface"
export TORCH_HOME="$SCRATCH/.cache/torch"
```

### Wandb not working

Check:
- `WANDB_API_KEY` is set in `.env`
- Proxy module is loaded if needed: `module load eth_proxy`
- Wandb is enabled in config: `wandb.enabled: true`

## Adding Dependencies

Use `uv` to manage dependencies:

```bash
# Add new package
uv add torch transformers

# Add dev dependency
uv add --dev pytest black

# Update dependencies
uv sync
```

## Git Integration

The template automatically tracks:
- Git commit hash
- Git branch
- Whether working directory is clean

This metadata is saved in `metadata.json` for reproducibility.

## License

Adapt this template for your research needs!

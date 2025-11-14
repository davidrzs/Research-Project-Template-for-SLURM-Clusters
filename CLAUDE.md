# Claude Code Guide for This Project

This document provides guidance for Claude Code when working with this ML experiment template.

## Project Overview

This is a template repository for running machine learning experiments on SLURM-based HPC clusters. Originally developed for ETH Zurich's Euler cluster, but designed to work on any SLURM cluster with minimal configuration. The project uses:

- **uv** for Python dependency management
- **YAML configs** with OmegaConf for experiment configuration
- **Python-based SLURM submission** via `submit.py`
- **Automatic output management** with timestamped directories
- **Integrated logging** and Weights & Biases tracking

## Key Patterns

### 1. Experiment Workflow

The standard workflow is:

1. Create a config file in `configs/` with SLURM params and experiment settings
2. Create an experiment script in `src/` that accepts `--config` and `--output-dir`
3. Submit with `python submit.py --config configs/your_config.yaml`
4. Results go to `outputs/{config_name}_{timestamp}_{uuid}/`

### 2. Configuration Structure

All configs should follow this pattern:

```yaml
script: src/your_script.py  # Required

slurm:  # SLURM parameters
  job_name: experiment_name
  time: "04:00:00"
  mem_per_cpu: "4G"
  cpus_per_task: 1
  gpus: null  # or "rtx_3090:1", "a100:2", etc.

# Your experiment parameters
seed: 42
# ... other params
```

### 3. Experiment Scripts

All experiment scripts should:

- Accept `--config` and `--output-dir` arguments
- Use `load_config()` from `src.utils`
- Use `setup_logging()` to log to both file and console
- Write `status.txt` with SUCCESS/FAILED
- Save results to the output directory

See `src/hello_world.py` for a complete example.

### 4. Utility Functions

The template provides utilities in `src/utils/`:

- `load_config(path)` - Load YAML config with OmegaConf
- `setup_logging(output_dir)` - Setup file + console logging
- `init_wandb(project, ...)` - Initialize wandb tracking
- `get_git_info()` - Get current git hash/branch
- `save_metadata(output_dir, ...)` - Save experiment metadata

### 5. Output Directory Structure

Each experiment run creates:

```
outputs/{config_name}_{timestamp}_{uuid}/
├── submit.sh          # Generated SLURM script (can be re-run)
├── config.yaml        # Copy of config used
├── metadata.json      # Git info, timestamp, job ID
├── slurm-{jobid}.out  # STDOUT from SLURM
├── slurm-{jobid}.err  # STDERR from SLURM
├── experiment.log     # Application logs
├── status.txt         # SUCCESS or FAILED
└── [results]          # Experiment outputs
```

## Common Tasks

### Creating a New Experiment

1. **Create config**: `configs/new_experiment.yaml`
2. **Create script**: `src/new_experiment.py` (copy from `hello_world.py`)
3. **Test locally**: `source load-env.sh && uv run src/new_experiment.py --config configs/new_experiment.yaml --output-dir test_output`
4. **Dry-run**: `python submit.py --config configs/new_experiment.yaml --dry-run`
5. **Submit**: `python submit.py --config configs/new_experiment.yaml`

### Running Parameter Sweeps

Use `batch_submit.py`:

```bash
# Create sweep configs (or do manually)
python batch_submit.py configs/sweep_*.yaml
```

Or manually:

```bash
for config in configs/sweep_*.yaml; do
  python submit.py --config $config
done
```

### Adding Dependencies

```bash
# Add package
uv add package-name

# Add dev dependency
uv add --dev package-name

# Sync environment
uv sync
```

### Checking Experiment Status

```bash
# Check running jobs
squeue -u $USER

# Check specific job
squeue -j JOB_ID

# View logs
tail -f outputs/experiment_*/slurm-*.out

# Check status of completed experiments
grep -r "SUCCESS\|FAILED" outputs/*/status.txt
```

## Important Notes

### Environment Setup

- **Always source `load-env.sh`** before running experiments locally
- Edit `load-env.sh` to load required modules (uncomment relevant lines)
- Ensure `.env` exists with API keys (`HF_TOKEN`, `WANDB_API_KEY`)

### Cache Directories

The template redirects caches to `$SCRATCH` to avoid home directory quota:

- Hugging Face models: `$SCRATCH/.cache/huggingface`
- PyTorch models: `$SCRATCH/.cache/torch`
- Wandb: `$SCRATCH/.cache/wandb`

These are set in `load-env.sh` and should NOT be changed unless you have a specific reason.

### Git Integration

The template automatically tracks git metadata. Ensure you commit changes before running experiments for proper reproducibility tracking.

### SLURM Parameters

Common SLURM settings:

- **GPU types**: `rtx_3090:1`, `a100:1`, `a100:2` (check cluster docs for available types)
- **Time format**: `HH:MM:SS` or `DD-HH:MM:SS`
- **Memory**: `4G`, `16G`, `32G`, etc.
- **Partitions**: Usually auto-assigned, but can specify if needed

### Troubleshooting

Common issues:

1. **Job fails immediately**: Check `slurm-*.err` and verify modules are loaded in `load-env.sh`
2. **Import errors**: Run `uv sync` to install dependencies
3. **Quota exceeded**: Verify caches are redirected to `$SCRATCH` in `load-env.sh`
4. **Wandb errors**: Check `WANDB_API_KEY` in `.env` and load `eth_proxy` module if needed

## File Editing Guidelines

When modifying this template:

### DO:

- Keep experiment scripts following the `--config` and `--output-dir` pattern
- Use OmegaConf for config loading (supports variable interpolation)
- Log important information (helps with debugging)
- Write status.txt to track success/failure
- Test locally before submitting to SLURM

### DON'T:

- Hardcode paths or parameters in scripts (use configs)
- Modify `submit.py` unless adding core functionality
- Change the output directory naming scheme (breaks reproducibility)
- Commit `.env` file (contains secrets)
- Commit `outputs/` directory (add to .gitignore)

## Code Style

- Follow existing patterns in `src/hello_world.py`
- Use type hints where helpful
- Keep utility functions in `src/utils/`
- Use descriptive variable names
- Add docstrings to functions

## Testing

Before submitting to SLURM:

```bash
# 1. Source environment
source load-env.sh

# 2. Test script locally with small data
uv run src/your_script.py \
  --config configs/your_config.yaml \
  --output-dir test_output

# 3. Check output
ls test_output/
cat test_output/status.txt

# 4. Dry-run submit
python submit.py --config configs/your_config.yaml --dry-run

# 5. Submit
python submit.py --config configs/your_config.yaml
```

## Additional Resources

- SLURM documentation: https://slurm.schedmd.com/documentation.html
- Weights & Biases: https://docs.wandb.ai/
- ETH Euler documentation (example cluster): https://scicomp.ethz.ch/wiki/Euler

## Questions?

If you're unsure about how to implement something, refer to:

1. `src/hello_world.py` - Complete example
2. `README.md` - Usage documentation
3. Existing configs in `configs/`
4. Utility functions in `src/utils/`

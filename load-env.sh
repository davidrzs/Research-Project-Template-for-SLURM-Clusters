#!/bin/bash
# Environment setup script for Slurm cluster
# Source this file before running experiments: source load-env.sh

# =============================================================================
# MODULE LOADING
# =============================================================================
# Load required modules for your experiments
# Check available modules with: module avail

# Example: Load Python with CUDA support
# module load stack/2024-06 python_cuda/3.11.6

# Example: Load specific Python version
# module load python/3.11.6

# Example: Load code-server for development
# module load code-server

# Example: Load proxy for external network access
# module load eth_proxy

# =============================================================================
# CACHE DIRECTORY REDIRECTION
# =============================================================================
# IMPORTANT: Redirect cache directories to $SCRATCH to avoid filling up
# home directory quota (typically 50GB limit).
# $SCRATCH has much larger quota (typically 2.5TB) but is NOT backed up.

# Hugging Face cache (models, datasets, tokenizers)
export HF_HOME="$SCRATCH/.cache/huggingface"

# PyTorch model cache
export TORCH_HOME="$SCRATCH/.cache/torch"

# Transformers cache
export TRANSFORMERS_CACHE="$SCRATCH/.cache/huggingface/transformers"

# Weights & Biases cache
export WANDB_CACHE_DIR="$SCRATCH/.cache/wandb"
export WANDB_DATA_DIR="$SCRATCH/.cache/wandb_data"

# Matplotlib cache
export MPLCONFIGDIR="$SCRATCH/.cache/matplotlib"

# Jupyter cache
export JUPYTER_DATA_DIR="$SCRATCH/.cache/jupyter"

# General Python cache
export PYTHONPYCACHEPREFIX="$SCRATCH/.cache/pycache"

# =============================================================================
# API KEYS AND TOKENS
# =============================================================================
# Load API keys from .env file
# Make sure you have created .env based on .env.example

if [ -f .env ]; then
    # Export variables from .env file
    set -a
    source .env
    set +a
else
    echo "Warning: .env file not found. API keys may not be set."
    echo "Copy .env.example to .env and fill in your API keys."
fi

# =============================================================================
# ENVIRONMENT VARIABLES
# =============================================================================
# Optional: Set additional environment variables

# Disable tokenizers parallelism warning (if using Hugging Face)
# export TOKENIZERS_PARALLELISM=false

# Set number of threads for numpy/pytorch (if needed)
# export OMP_NUM_THREADS=4
# export MKL_NUM_THREADS=4

# =============================================================================
# VERIFICATION
# =============================================================================
# Print loaded modules and cache locations for verification
echo "Environment setup complete!"
echo "Loaded modules: $(module list 2>&1 | grep -v 'Currently Loaded' | grep -v '^$' || echo 'None')"
echo "Cache directory: $SCRATCH/.cache"
echo "HF_HOME: $HF_HOME"
echo "WANDB_CACHE_DIR: $WANDB_CACHE_DIR"

# Check if .env file was loaded
if [ -n "$HF_TOKEN" ]; then
    echo "HF_TOKEN: Set (${#HF_TOKEN} characters)"
else
    echo "HF_TOKEN: Not set"
fi

if [ -n "$WANDB_API_KEY" ]; then
    echo "WANDB_API_KEY: Set (${#WANDB_API_KEY} characters)"
else
    echo "WANDB_API_KEY: Not set"
fi

#!/bin/bash
# Fieldream launcher - activates venv and sets up HuggingFace for offline operation

# Activate venv
source ~/fieldream_env/bin/activate

# Set HuggingFace cache to venv (makes app portable and offline)
export HF_HOME="$VIRTUAL_ENV/huggingface_cache"
export TRANSFORMERS_CACHE="$VIRTUAL_ENV/huggingface_cache"
export HF_DATASETS_CACHE="$VIRTUAL_ENV/huggingface_cache"

# Enable offline mode - don't try to download from internet
export HF_DATASETS_OFFLINE=1
export TRANSFORMERS_OFFLINE=0  # Set to 1 if you want strict offline (no remote access)

# Run Fieldream
python main.py

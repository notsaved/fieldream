#!/bin/bash
# Setup script to download and cache BLIP model for Fieldream Snapshot ream
# This must be run ONCE before using Snapshot with descriptions
# All downloads go into the venv, making the app 100% portable and offline

set -e

echo "=== Fieldream BLIP Offline Setup ==="
echo

# Activate venv
echo "1. Activating Python environment..."
source ~/fieldream_env/bin/activate

# Set up cache directory IN the venv (not in home)
export HF_HOME="$VIRTUAL_ENV/huggingface_cache"
export TRANSFORMERS_CACHE="$VIRTUAL_ENV/huggingface_cache"
export HF_DATASETS_CACHE="$VIRTUAL_ENV/huggingface_cache"
mkdir -p "$HF_HOME"

echo "   Cache will be stored in: $HF_HOME"
echo

# Install pillow if needed
echo "2. Installing/checking Pillow..."
pip install pillow -q

# Download and cache BLIP model and tokenizers
echo "3. Downloading BLIP model and tokenizers to venv (may take 5-10 minutes)..."
echo "   This will be saved to your venv, making it fully portable"
echo

python << 'PYTHON_EOF'
import os
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch

hf_home = os.environ.get('HF_HOME')
print(f"   Cache location: {hf_home}")
print()

print("   - Downloading processor and tokenizers...")
processor = BlipProcessor.from_pretrained('Salesforce/blip-image-captioning-base')
print("      ✓ Processor and tokenizers cached")

print("   - Downloading model weights...")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = BlipForConditionalGeneration.from_pretrained(
    'Salesforce/blip-image-captioning-base',
    device_map=device
)
print("      ✓ Model cached")

print()
print("   Testing offline load (no internet)...")
os.environ['HF_DATASETS_OFFLINE'] = '1'
processor_offline = BlipProcessor.from_pretrained(
    'Salesforce/blip-image-captioning-base',
    local_files_only=True
)
model_offline = BlipForConditionalGeneration.from_pretrained(
    'Salesforce/blip-image-captioning-base',
    device_map=device,
    local_files_only=True
)
print("      ✓ Works offline!")

PYTHON_EOF

echo
echo "=== Setup Complete ==="
echo "BLIP is now cached in your venv and works 100% OFFLINE"
echo
echo "Your Fieldream is now:"
echo "  ✓ Fully portable (entire venv is self-contained)"
echo "  ✓ Works offline anywhere (no internet needed)"
echo "  ✓ No more HuggingFace downloads or warnings"
echo
echo "Next: Start Fieldream with: ./run.sh"

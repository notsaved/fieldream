#!/bin/bash
# Setup script to download and cache BLIP model for Fieldream Snapshot ream

set -e

echo "=== Fieldream BLIP Setup ==="
echo

# Activate venv
echo "1. Activating Python environment..."
source ~/fieldream_env/bin/activate

# Install pillow if needed
echo "2. Installing/checking Pillow..."
pip install pillow -q

# Download and cache BLIP model
echo "3. Downloading BLIP model (may take a few minutes)..."
python << 'PYTHON_EOF'
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch

print("   - Downloading processor...")
processor = BlipProcessor.from_pretrained('Salesforce/blip-image-captioning-base')

print("   - Downloading model...")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = BlipForConditionalGeneration.from_pretrained(
    'Salesforce/blip-image-captioning-base',
    device_map=device
)

print("   - BLIP model cached successfully!")
PYTHON_EOF

echo
echo "=== Setup Complete ==="
echo "BLIP is now ready for image captioning in Fieldream!"
echo
echo "Next: Start Fieldream with: ./run.sh"

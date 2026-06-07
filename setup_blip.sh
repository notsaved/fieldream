#!/bin/bash
# Setup script to download and cache BLIP model for Fieldream Snapshot ream
# This must be run ONCE before using Snapshot with descriptions

set -e

echo "=== Fieldream BLIP Offline Setup ==="
echo

# Activate venv
echo "1. Activating Python environment..."
source ~/fieldream_env/bin/activate

# Install pillow if needed
echo "2. Installing/checking Pillow..."
pip install pillow -q

# Download and cache BLIP model - THIS MUST COMPLETE SUCCESSFULLY
echo "3. Downloading BLIP model to cache (may take 5-10 minutes)..."
echo "   This will be saved to ~/.cache/huggingface/"
echo "   After this, Fieldream will work ENTIRELY OFFLINE"
echo

python << 'PYTHON_EOF'
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
import os

print("   - Downloading processor...")
processor = BlipProcessor.from_pretrained('Salesforce/blip-image-captioning-base')
print("      ✓ Processor cached")

print("   - Downloading model weights...")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = BlipForConditionalGeneration.from_pretrained(
    'Salesforce/blip-image-captioning-base',
    device_map=device
)
print("      ✓ Model cached")

# Verify cache exists
cache_dir = os.path.expanduser("~/.cache/huggingface/")
if os.path.exists(cache_dir):
    print(f"   - Cache directory: {cache_dir}")
    print("      ✓ BLIP model is now cached for offline use")
else:
    print("   ! Warning: Cache not found, something went wrong")

print()
print("   Testing offline load (local_files_only=True)...")
processor_offline = BlipProcessor.from_pretrained(
    'Salesforce/blip-image-captioning-base',
    local_files_only=True
)
model_offline = BlipForConditionalGeneration.from_pretrained(
    'Salesforce/blip-image-captioning-base',
    device_map=device,
    local_files_only=True
)
print("      ✓ Offline mode works!")

PYTHON_EOF

echo
echo "=== Setup Complete ==="
echo "BLIP is now cached and ready for OFFLINE use in Fieldream!"
echo
echo "Snapshot descriptions will now:"
echo "  1. Capture image instantly"
echo "  2. Generate description using cached BLIP (no internet needed)"
echo "  3. Save to snapshot.md with ethnographic analysis"
echo
echo "Next: Start Fieldream with: ./run.sh"

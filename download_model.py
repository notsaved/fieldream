#!/usr/bin/env python3
"""Pre-download and cache LLaVA model for Snapshot ream."""

import sys
from pathlib import Path

def download_model():
    """Download and cache the LLaVA model."""
    try:
        from transformers import AutoProcessor, LlavaForConditionalGeneration
        import torch
        
        print("🔄 Downloading LLaVA model... this may take 5-10 minutes")
        print("   Model size: ~16GB (will be cached in ~/.cache/huggingface/)")
        
        model_name = "llava-hf/llava-1.5-7b-hf"
        
        print(f"\n📥 Downloading processor...")
        processor = AutoProcessor.from_pretrained(model_name)
        
        print(f"📥 Downloading model (this is the large part)...")
        vision_model = LlavaForConditionalGeneration.from_pretrained(
            model_name,
            device_map="cpu",
            load_in_8bit=True,
            torch_dtype=torch.float32
        )
        
        print("\n✅ Model downloaded and cached successfully!")
        print(f"   Location: ~/.cache/huggingface/hub/")
        print(f"\n💾 You can now run fieldream without waiting for model download.")
        return True
        
    except ImportError as e:
        print(f"❌ Error: Missing dependency: {e}")
        print("\n📦 Install dependencies first:")
        print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu")
        print("   pip install transformers accelerate bitsandbytes opencv-python pillow")
        return False
    
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("LLaVA Model Pre-Download Script")
    print("=" * 60)
    
    success = download_model()
    sys.exit(0 if success else 1)

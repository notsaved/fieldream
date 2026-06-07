"""Snapshot ream - Image capture and vision-based description generation."""

import threading
import queue
import time
from datetime import datetime, timedelta
from pathlib import Path

from reams.base import BaseRea
from utils.file_handler import FileHandler


class SnapshotRea(BaseRea):
    """Snapshot ream for webcam image capture and vision-language description."""
    
    def __init__(self, file_handler: FileHandler):
        """Initialize snapshot ream.
        
        Args:
            file_handler: FileHandler instance for file operations
        """
        super().__init__(file_handler, "snapshot", "Snapshot")
        self.is_recording = False
        self.capture_thread = None
        self.process_thread = None
        self.image_queue = queue.Queue()
        self.vision_model = None
        self.processor = None
        
        # Interval management
        self.interval_options = [5, 10, 15, 20, 30]  # minutes
        self.current_interval_idx = 1  # Start with 10 minutes
        self.next_snapshot_time = None
        
        # Status
        self.error_message = ""
        self.last_description = ""
        self.device_info = ""
        self.minutes_until_next = 0
        self.is_processing = False
        self.snapshot_count = 0
        
        # Load prompt from file
        self.ethnographic_prompt = self._load_prompt()
    
    def get_help_text(self) -> str:
        """Get help text for snapshot ream."""
        return "Ctrl+P: Capture now | ↑↓: Change interval (5-30 min)"
    
    def handle_input(self, input_data: str) -> None:
        """Handle input data (not used for snapshot)."""
        pass
    
    def _load_prompt(self) -> str:
        """Load ethnographic prompt from file."""
        try:
            prompt_file = Path(__file__).parent.parent / "prompts" / "snapshot_prompt.txt"
            if prompt_file.exists():
                return prompt_file.read_text(encoding="utf-8").strip()
            else:
                return "Describe this scene in detail."
        except:
            return "Describe this scene in detail."
    
    def _load_model(self) -> None:
        """Lazy-load the LLaVA model (called from worker thread, not UI thread)."""
        if self.vision_model is not None:
            return  # Already loaded
        
        try:
            from transformers import AutoProcessor, LlavaForConditionalGeneration
            import torch
            
            model_name = "llava-hf/llava-1.5-7b-hf"
            self.device_info = "Loading model (first snapshot only)..."
            
            self.processor = AutoProcessor.from_pretrained(model_name)
            self.vision_model = LlavaForConditionalGeneration.from_pretrained(
                model_name,
                device_map="cpu",
                load_in_8bit=True,
                torch_dtype=torch.float32
            )
            self.device_info = "Model loaded"
        except Exception as e:
            self.error_message = f"Model load failed: {str(e)[:40]}"
            self.vision_model = None
    
    def set_interval(self, direction: str) -> None:
        """Change snapshot interval.
        
        Args:
            direction: "up" or "down" to cycle through intervals
        """
        if direction == "up":
            self.current_interval_idx = (self.current_interval_idx + 1) % len(self.interval_options)
        elif direction == "down":
            self.current_interval_idx = (self.current_interval_idx - 1) % len(self.interval_options)
        
        # Reset next snapshot time with new interval
        if self.is_recording:
            self.next_snapshot_time = datetime.now() + timedelta(minutes=self.interval_options[self.current_interval_idx])
    
    def get_current_interval(self) -> int:
        """Get current interval in minutes."""
        return self.interval_options[self.current_interval_idx]
    
    def trigger_manual_snapshot(self) -> None:
        """Manually trigger a snapshot immediately."""
        if self.is_recording and not self.is_processing:
            # Wake up capture thread immediately
            self.next_snapshot_time = datetime.now()
    
    def start_session(self) -> None:
        """Start a new snapshot session (webcam capture)."""
        super().start_session()
        self.is_recording = True
        self.snapshot_count = 0
        self.error_message = ""
        self.device_info = "Ready (model loads on first snapshot)"
        self.is_processing = False
        self.next_snapshot_time = datetime.now() + timedelta(minutes=self.get_current_interval())
        
        try:
            import cv2
        except ImportError as e:
            self.error_message = f"Missing: opencv-python"
            self.is_recording = False
            return
        
        # Don't load model yet - will lazy-load on first snapshot
        # This prevents UI freeze when enabling snapshot mode
        
        # Start background threads
        self.capture_thread = threading.Thread(target=self._capture_scheduler, daemon=True)
        self.capture_thread.start()
        
        self.process_thread = threading.Thread(target=self._process_worker, daemon=True)
        self.process_thread.start()
    
    def _capture_scheduler(self) -> None:
        """Background thread: schedule and capture images."""
        try:
            import cv2
        except ImportError:
            self.error_message = "OpenCV not available"
            return
        
        while self.is_recording:
            try:
                # Check if it's time for a snapshot
                now = datetime.now()
                if now >= self.next_snapshot_time and not self.is_processing:
                    # Capture image
                    try:
                        cap = cv2.VideoCapture(0)
                        if cap.isOpened():
                            ret, frame = cap.read()
                            cap.release()
                            
                            if ret and frame is not None:
                                self.image_queue.put(frame)
                                self.is_processing = True
                                self.snapshot_count += 1
                                self.device_info = f"Captured snapshot #{self.snapshot_count}, processing..."
                            else:
                                self.error_message = "Failed to capture frame"
                        else:
                            self.error_message = "Camera not available"
                    except Exception as e:
                        self.error_message = f"Capture error: {str(e)[:20]}"
                    
                    # Schedule next snapshot
                    self.next_snapshot_time = datetime.now() + timedelta(minutes=self.get_current_interval())
                
                # Update countdown
                if self.next_snapshot_time:
                    delta = self.next_snapshot_time - datetime.now()
                    self.minutes_until_next = max(0, int(delta.total_seconds() / 60))
                
                time.sleep(1)  # Check every second
            except Exception as e:
                self.error_message = f"Scheduler error: {str(e)[:20]}"
    
    def _process_worker(self) -> None:
        """Background thread: process images with vision model."""
        try:
            from PIL import Image
            import torch
        except ImportError as e:
            self.error_message = f"Missing: {str(e)[:20]}"
            return
        
        while self.is_recording or not self.image_queue.empty():
            try:
                # Get image with timeout
                image_frame = self.image_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            try:
                # Lazy-load model on first use (not on startup)
                if self.vision_model is None:
                    self._load_model()
                    if self.vision_model is None:
                        self.error_message = "Failed to load model"
                        continue
                
                # Convert OpenCV frame (BGR numpy array) to PIL Image (RGB)
                import cv2
                rgb_frame = cv2.cvtColor(image_frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_frame)
                
                # Process image with vision model
                prompt = self.ethnographic_prompt
                inputs = self.processor(
                    text=prompt,
                    images=pil_image,
                    return_tensors="pt"
                )
                
                # Generate description
                with torch.no_grad():
                    output = self.vision_model.generate(
                        **inputs,
                        max_new_tokens=300,
                        temperature=0.7
                    )
                
                description = self.processor.decode(output[0], skip_special_tokens=True)
                # Extract just the generated text (after prompt)
                if "Assistant:" in description:
                    description = description.split("Assistant:")[-1].strip()
                
                # Save to file with timestamp
                self.last_description = description
                self.save_entry(description)
                self.device_info = f"Processed {self.snapshot_count} snapshots"
                
            except Exception as e:
                self.error_message = f"Process error: {str(e)[:30]}"
            finally:
                self.is_processing = False
    
    def end_session(self) -> None:
        """End snapshot session."""
        self.is_recording = False
        super().end_session()

"""Snapshot ream - Simple webcam image capture with LLaVA descriptions."""

import threading
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

from reams.base import BaseRea
from utils.file_handler import FileHandler


class SnapshotRea(BaseRea):
    """Snapshot ream for webcam image capture with AI descriptions."""
    
    def __init__(self, file_handler: FileHandler):
        """Initialize snapshot ream.
        
        Args:
            file_handler: FileHandler instance for file operations
        """
        super().__init__(file_handler, "snapshot", "Snapshot")
        
        # Status fields - all initialized
        self.is_recording = False
        self.error_message = ""
        self.device_info = ""
        self.minutes_until_next = 0
        self.snapshot_count = 0
        self.describing_count = 0  # Number of images being described
        
        # Interval management
        self.interval_options = [5, 10, 15, 20, 30]  # minutes
        self.current_interval_idx = 1  # Start with 10 minutes
        self.next_snapshot_time = None
        
        self.capture_thread = None
        self.describe_thread = None
        self.pending_images = []  # Queue of image paths needing descriptions
        self.describe_lock = threading.Lock()
    
    def get_help_text(self) -> str:
        """Get help text for snapshot ream."""
        return "Ctrl+P: Capture now | ↑↓: Change interval (5-30 min) | Alt+P: Capture now"
    
    def handle_input(self, input_data: str) -> None:
        """Handle input data (not used for snapshot)."""
        pass
    
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
        
        interval = self.interval_options[self.current_interval_idx]
        self.device_info = f"Interval: {interval}m"
    
    def get_current_interval(self) -> int:
        """Get current interval in minutes."""
        return self.interval_options[self.current_interval_idx]
    
    def trigger_manual_snapshot(self) -> None:
        """Manually trigger a snapshot immediately."""
        if self.is_recording:
            self.next_snapshot_time = datetime.now()
    
    def start_session(self) -> None:
        """Start snapshot session. MINIMAL - no blocking operations."""
        # Step 1: Set flags (super fast)
        self.is_recording = True
        self.snapshot_count = 0
        self.describing_count = 0
        self.error_message = ""
        self.device_info = "Init..."
        self.next_snapshot_time = datetime.now() + timedelta(minutes=self.get_current_interval())
        
        # Step 2: Initialize file handler (should be fast)
        try:
            super().start_session()
        except Exception as e:
            self.error_message = f"File error: {str(e)[:15]}"
        
        # Step 3: Start background threads (non-blocking daemon)
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        self.describe_thread = threading.Thread(target=self._describe_loop, daemon=True)
        self.describe_thread.start()
        
        self.device_info = "Ready"
    
    def end_session(self) -> None:
        """End the session."""
        self.is_recording = False
        try:
            super().end_session()
        except:
            pass
    
    def _capture_loop(self) -> None:
        """Background thread: capture images on schedule. SAFE - all errors caught."""
        while self.is_recording:
            try:
                # Update timer
                if self.next_snapshot_time:
                    delta = self.next_snapshot_time - datetime.now()
                    self.minutes_until_next = max(0, int(delta.total_seconds() / 60))
                
                # Check if time for snapshot
                if datetime.now() >= self.next_snapshot_time:
                    filepath = self._do_capture()
                    if filepath:
                        # Queue image for description
                        with self.describe_lock:
                            self.pending_images.append(filepath)
                    self.next_snapshot_time = datetime.now() + timedelta(minutes=self.get_current_interval())
                
                time.sleep(1)
            except:
                pass
    
    def _do_capture(self) -> str:
        """Actually capture image. Returns filepath if successful."""
        try:
            import cv2
            
            # Verify session folder exists
            if not self.file_handler or not self.file_handler.session_folder:
                self.error_message = "No session folder"
                return None
            
            # Open camera
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.error_message = "Camera failed"
                return None
            
            # Read frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                self.error_message = "Frame read failed"
                return None
            
            # Save image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snapshot_{timestamp}.jpg"
            filepath = self.file_handler.session_folder / filename
            
            cv2.imwrite(str(filepath), frame)
            self.snapshot_count += 1
            self.device_info = f"Captured #{self.snapshot_count}"
            self.error_message = ""
            return str(filepath)
        
        except Exception as e:
            self.error_message = f"Capture: {str(e)[:15]}"
            return None
    
    def _describe_loop(self) -> None:
        """Background thread: generate descriptions for pending images."""
        while self.is_recording:
            try:
                # Check if there are images to describe
                with self.describe_lock:
                    if not self.pending_images:
                        time.sleep(0.5)
                        continue
                    filepath = self.pending_images.pop(0)
                
                self.describing_count += 1
                self._generate_description(filepath)
                self.describing_count = max(0, self.describing_count - 1)
            
            except:
                self.describing_count = max(0, self.describing_count - 1)
                time.sleep(1)
    
    def _generate_description(self, image_path: str) -> None:
        """Generate description using LLaVA model."""
        try:
            from transformers import AutoProcessor, LlavaForConditionalGeneration
            from PIL import Image
            
            # Load image
            image = Image.open(image_path)
            
            # Load model (should be cached after first load)
            processor = AutoProcessor.from_pretrained("llava-hf/llava-1.5-7b-hf")
            model = LlavaForConditionalGeneration.from_pretrained(
                "llava-hf/llava-1.5-7b-hf",
                device_map="auto"
            )
            
            # Generate prompt
            prompt = "Describe what you see in this image in one sentence."
            inputs = processor(text=prompt, images=image, return_tensors="pt")
            
            # Generate description
            output = model.generate(**inputs, max_new_tokens=50)
            description = processor.decode(output[0], skip_special_tokens=True)
            
            # Save description as JSON metadata
            image_base = Path(image_path).stem
            json_path = Path(image_path).parent / f"{image_base}.json"
            
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "image_file": Path(image_path).name,
                "description": description
            }
            
            with open(json_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.device_info = f"Captured #{self.snapshot_count}, described"
        
        except Exception as e:
            self.error_message = f"Describe: {str(e)[:15]}"

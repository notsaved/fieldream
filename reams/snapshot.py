"""Snapshot ream - Webcam image capture with ethnographic descriptions using BLIP."""

import threading
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

from reams.base import BaseRea
from utils.file_handler import FileHandler


class SnapshotRea(BaseRea):
    """Snapshot ream for webcam image capture with AI ethnographic descriptions."""
    
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
        self.describing_count = 0
        self.content = ""  # Accumulated descriptions for display
        
        # Interval management
        self.interval_options = [5, 10, 15, 20, 30]  # minutes
        self.current_interval_idx = 1  # Start with 10 minutes
        self.next_snapshot_time = None
        
        self.capture_thread = None
        self.describe_thread = None
        self.pending_images = []
        self.describe_lock = threading.Lock()
        self.manual_trigger_pending = False  # Flag for manual captures to bypass interval
    
    def get_help_text(self) -> str:
        """Get help text for snapshot ream."""
        return "Ctrl+P: Capture now | ↑↓: Change interval (5-30 min) | Alt+P: Capture now"
    
    def handle_input(self, input_data: str) -> None:
        """Handle input data (not used for snapshot)."""
        pass
    
    def set_interval(self, direction: str) -> None:
        """Change snapshot interval."""
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
            self.manual_trigger_pending = True
    
    def start_session(self) -> None:
        """Start snapshot session."""
        # Step 1: Set flags
        self.is_recording = True
        self.snapshot_count = 0
        self.describing_count = 0
        self.error_message = ""
        self.device_info = ""  # Will show timer
        self.content = ""
        self.next_snapshot_time = datetime.now() + timedelta(minutes=self.get_current_interval())
        
        # Step 2: Initialize file handler
        try:
            super().start_session()
        except Exception as e:
            self.error_message = f"File error: {str(e)[:15]}"
        
        # Step 3: Start background threads
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        self.describe_thread = threading.Thread(target=self._describe_loop, daemon=True)
        self.describe_thread.start()
    
    def end_session(self) -> None:
        """End the session."""
        self.is_recording = False
        self.manual_trigger_pending = False
        try:
            super().end_session()
        except:
            pass
    
    def _capture_loop(self) -> None:
        """Background thread: capture images on schedule."""
        while self.is_recording:
            try:
                # Update timer display
                if self.next_snapshot_time:
                    delta = self.next_snapshot_time - datetime.now()
                    self.minutes_until_next = max(0, int(delta.total_seconds() / 60))
                    self.device_info = f"Next: {self.minutes_until_next}m"
                
                # Check for manual trigger (no cooldown) or scheduled time
                should_capture = (
                    self.manual_trigger_pending or
                    (datetime.now() >= self.next_snapshot_time)
                )
                
                if should_capture:
                    filepath = self._do_capture()
                    if filepath:
                        self.device_info = "[snap!]"
                        # Queue image for description
                        with self.describe_lock:
                            self.pending_images.append(filepath)
                    # Reset both timers
                    self.next_snapshot_time = datetime.now() + timedelta(minutes=self.get_current_interval())
                    self.manual_trigger_pending = False
                
                time.sleep(0.2)  # Check more frequently for manual triggers
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
            
            # Try to find available camera
            camera_index = None
            for i in range(0, 5):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    camera_index = i
                    cap.release()
                    break
            
            if camera_index is None:
                self.error_message = "No camera found"
                return None
            
            # Open camera
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                self.error_message = f"Camera {camera_index} failed"
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
            self.error_message = ""
            return str(filepath)
        
        except Exception as e:
            self.error_message = f"Capture: {str(e)[:15]}"
            return None
    
    def _describe_loop(self) -> None:
        """Background thread: generate descriptions for pending images."""
        # Load model ONCE at start of thread (not for each image)
        processor = None
        model = None
        device = None
        model_error = False
        
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            import torch
            
            processor = BlipProcessor.from_pretrained(
                'Salesforce/blip-image-captioning-base',
                local_files_only=True
            )
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = BlipForConditionalGeneration.from_pretrained(
                'Salesforce/blip-image-captioning-base',
                device_map=device,
                local_files_only=True
            )
        except Exception as e:
            self.error_message = f"Model error: {str(e)[:15]}"
            model_error = True
        
        # Now process images (model stays loaded in memory)
        while self.is_recording:
            try:
                if model_error:
                    time.sleep(1)
                    continue
                
                # Check if there are images to describe
                with self.describe_lock:
                    if not self.pending_images:
                        time.sleep(0.5)
                        continue
                    filepath = self.pending_images.pop(0)
                
                self.describing_count += 1
                self.device_info = "processing"
                self._generate_description(filepath, processor, model, device)
                self.describing_count = max(0, self.describing_count - 1)
                
                # Reset to timer display
                if self.next_snapshot_time:
                    delta = self.next_snapshot_time - datetime.now()
                    self.minutes_until_next = max(0, int(delta.total_seconds() / 60))
                    self.device_info = f"Next: {self.minutes_until_next}m"
            
            except Exception as e:
                self.error_message = f"Error: {str(e)[:20]}"
                self.describing_count = max(0, self.describing_count - 1)
                time.sleep(1)
    
    def _generate_description(self, image_path: str, processor, model, device) -> None:
        """Generate detailed description using pre-loaded BLIP model (reused across images)."""
        try:
            from PIL import Image
            
            # Load image only
            image = Image.open(image_path)
            
            # Use conditional text to encourage detailed descriptions
            conditional_text = "Describe in detail:"
            inputs = processor(
                image, 
                text=conditional_text,
                return_tensors="pt"
            ).to(device)
            
            # Generate with parameters for longer, more detailed output
            out = model.generate(
                **inputs,
                max_length=200,          # Increased from 100
                min_length=50,           # Force at least 50 tokens
                length_penalty=2.0,      # Encourage longer sequences
                num_beams=4,             # Better quality (more computational)
                temperature=0.7,         # More varied output
            )
            description = processor.decode(out[0], skip_special_tokens=True)
            
            # Clean up - remove the conditional text if it appears
            if description.startswith(conditional_text):
                description = description[len(conditional_text):].strip()
            
            # Create formatted entry for snapshot notes
            timestamp = datetime.now().strftime("%H:%M:%S")
            filename = Path(image_path).name
            entry = f"\n**{timestamp}** - {filename}\n{description}\n"
            
            # Save to snapshot notes
            self.save_entry(entry)
            self.content += entry
            
            # Also save image metadata JSON
            image_base = Path(image_path).stem
            json_path = Path(image_path).parent / f"{image_base}.json"
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "image_file": filename,
                "description": description
            }
            with open(json_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.error_message = ""
        
        except Exception as e:
            self.error_message = f"Describe: {str(e)[:20]}"
            try:
                entry = f"\n**{datetime.now().strftime('%H:%M:%S')}** - {Path(image_path).name}\n[Error: {self.error_message}]\n"
                self.save_entry(entry)
            except:
                pass

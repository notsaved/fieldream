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
            self.device_info = "Loading processor..."
            self.processor = AutoProcessor.from_pretrained(model_name)
            
            self.device_info = "Loading vision model..."
            self.vision_model = LlavaForConditionalGeneration.from_pretrained(
                model_name,
                device_map="cpu",
                load_in_8bit=True,
                torch_dtype=torch.float32
            )
            self.device_info = "Model ready"
        except ImportError as e:
            self.error_message = f"Import error: {str(e)[:30]}"
            self.device_info = "Failed: missing dependency"
        except Exception as e:
            self.error_message = f"Load failed: {str(e)[:30]}"
            self.device_info = "Failed: load error"
    
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
        self.device_info = "Initialized (ready to capture)"
        self.is_processing = False
        self.next_snapshot_time = datetime.now() + timedelta(minutes=self.get_current_interval())
        
        try:
            import cv2
        except ImportError as e:
            self.error_message = f"Missing: opencv-python"
            self.is_recording = False
            return
        
        # Start threads in background (daemon mode so they don't block shutdown)
        try:
            self.capture_thread = threading.Thread(target=self._capture_scheduler, daemon=True, name="SnapshotCapture")
            self.capture_thread.start()
            
            self.process_thread = threading.Thread(target=self._process_worker, daemon=True, name="SnapshotProcess")
            self.process_thread.start()
            
            self.device_info = "Threads started"
        except Exception as e:
            self.error_message = f"Thread error: {str(e)[:30]}"
            self.is_recording = False
    
    def _capture_scheduler(self) -> None:
        """Background thread: schedule and capture images."""
        try:
            import cv2
        except ImportError:
            self.error_message = "OpenCV not available"
            return
        
        while self.is_recording:
            try:
                # Update countdown timer
                if self.next_snapshot_time:
                    delta = self.next_snapshot_time - datetime.now()
                    self.minutes_until_next = max(0, int(delta.total_seconds() / 60))
                
                # Check if it's time for a snapshot (and not already processing)
                now = datetime.now()
                if now >= self.next_snapshot_time and not self.is_processing:
                    try:
                        # Open camera
                        cap = cv2.VideoCapture(0)
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffering
                        
                        if not cap.isOpened():
                            self.error_message = "Camera unavailable"
                        else:
                            ret, frame = cap.read()
                            cap.release()
                            
                            if ret and frame is not None and frame.size > 0:
                                self.image_queue.put(frame)
                                self.is_processing = True
                                self.snapshot_count += 1
                                self.device_info = f"Snapshot #{self.snapshot_count} captured"
                            else:
                                self.error_message = "Failed to read frame"
                        
                        # Schedule next snapshot
                        self.next_snapshot_time = datetime.now() + timedelta(minutes=self.get_current_interval())
                    
                    except Exception as e:
                        self.error_message = f"Capture: {str(e)[:25]}"
                
                time.sleep(1)
                
            except Exception as e:
                self.error_message = f"Scheduler: {str(e)[:25]}"
                time.sleep(1)
    
    def _process_worker(self) -> None:
        """Background thread: process images with vision model."""
        try:
            from PIL import Image
            import torch
            import cv2
        except ImportError as e:
            self.error_message = f"Missing import: {str(e)[:20]}"
            return
        
        while self.is_recording or not self.image_queue.empty():
            try:
                # Get image with timeout
                try:
                    image_frame = self.image_queue.get(timeout=2)
                except queue.Empty:
                    continue
                
                # Lazy-load model on first use
                if self.vision_model is None:
                    self.device_info = "Loading model..."
                    self._load_model()
                    if self.vision_model is None:
                        self.device_info = "Model load failed"
                        continue
                
                # Convert frame
                try:
                    rgb_frame = cv2.cvtColor(image_frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(rgb_frame)
                except Exception as e:
                    self.error_message = f"Frame convert: {str(e)[:20]}"
                    self.is_processing = False
                    continue
                
                # Generate description
                try:
                    prompt = self.ethnographic_prompt
                    inputs = self.processor(
                        text=prompt,
                        images=pil_image,
                        return_tensors="pt"
                    )
                    
                    with torch.no_grad():
                        output = self.vision_model.generate(
                            **inputs,
                            max_new_tokens=300,
                            temperature=0.7
                        )
                    
                    description = self.processor.decode(output[0], skip_special_tokens=True)
                    if "Assistant:" in description:
                        description = description.split("Assistant:")[-1].strip()
                    
                    # Save to file
                    self.last_description = description[:100]  # Store first 100 chars
                    self.save_entry(description)
                    self.device_info = f"Snapshot #{self.snapshot_count} saved"
                    
                except Exception as e:
                    self.error_message = f"Generation: {str(e)[:30]}"
                    self.device_info = "Error during generation"
                
            except Exception as e:
                self.error_message = f"Worker error: {str(e)[:30]}"
            
            finally:
                self.is_processing = False
        
        # Clean shutdown
        self.device_info = "Worker stopped"
    
    def end_session(self) -> None:
        """End snapshot session."""
        self.is_recording = False
        super().end_session()

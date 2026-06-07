"""Snapshot ream - Simple webcam image capture."""

import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from reams.base import BaseRea
from utils.file_handler import FileHandler


class SnapshotRea(BaseRea):
    """Snapshot ream for simple webcam image capture."""
    
    def __init__(self, file_handler: FileHandler):
        """Initialize snapshot ream.
        
        Args:
            file_handler: FileHandler instance for file operations
        """
        super().__init__(file_handler, "snapshot", "Snapshot")
        self.is_recording = False
        self.capture_thread = None
        
        # Interval management
        self.interval_options = [5, 10, 15, 20, 30]  # minutes
        self.current_interval_idx = 1  # Start with 10 minutes
        self.next_snapshot_time = None
        
        # Status - MUST all be initialized to avoid AttributeError
        self.error_message = ""
        self.device_info = ""
        self.minutes_until_next = 0
        self.snapshot_count = 0
    
    def get_help_text(self) -> str:
        """Get help text for snapshot ream."""
        return "Ctrl+P: Capture now | ↑↓: Change interval (5-30 min)"
    
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
            # Wake up capture thread immediately
            self.next_snapshot_time = datetime.now()
    
    def start_session(self) -> None:
        """Start a new snapshot session (webcam capture)."""
        try:
            # Initialize all attributes first (safe)
            self.is_recording = True
            self.snapshot_count = 0
            self.error_message = ""
            self.device_info = "Starting..."
            self.next_snapshot_time = datetime.now() + timedelta(minutes=self.get_current_interval())
            self.minutes_until_next = self.get_current_interval()
            
            # Then call super.start_session() which creates files (may fail)
            try:
                super().start_session()
            except Exception as e:
                self.error_message = f"File init: {str(e)[:20]}"
                self.device_info = "File error"
            
            # Start capture thread (daemon mode) - non-blocking
            try:
                self.capture_thread = threading.Thread(
                    target=self._capture_loop, 
                    daemon=True, 
                    name="SnapshotCapture"
                )
                self.capture_thread.start()
                self.device_info = "Ready"
            except Exception as e:
                self.error_message = f"Thread: {str(e)[:20]}"
                self.is_recording = False
        except Exception as e:
            # Catch-all - never crash the UI thread
            self.error_message = f"Init: {str(e)[:20]}"
            self.is_recording = False
            self.device_info = "Failed"
    
    def end_session(self) -> None:
        """End the session."""
        super().end_session()
        self.is_recording = False
    
    def _capture_loop(self) -> None:
        """Background thread: capture images on schedule."""
        try:
            import cv2
        except ImportError:
            self.error_message = "OpenCV not available"
            return
        
        while self.is_recording:
            try:
                # Check if session folder is valid
                if not self.file_handler or not self.file_handler.session_folder:
                    self.error_message = "Session folder not set"
                    time.sleep(1)
                    continue
                
                # Update countdown timer
                if self.next_snapshot_time:
                    delta = self.next_snapshot_time - datetime.now()
                    self.minutes_until_next = max(0, int(delta.total_seconds() / 60))
                
                # Check if it's time for a snapshot
                now = datetime.now()
                if now >= self.next_snapshot_time:
                    try:
                        # Open camera and capture
                        cap = cv2.VideoCapture(0)
                        if not cap.isOpened():
                            self.error_message = "Camera not found"
                        else:
                            ret, frame = cap.read()
                            cap.release()
                            
                            if ret and frame is not None:
                                # Save image
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"snapshot_{timestamp}.jpg"
                                filepath = self.file_handler.session_folder / filename
                                
                                cv2.imwrite(str(filepath), frame)
                                self.snapshot_count += 1
                                self.device_info = f"Snapshot #{self.snapshot_count} saved"
                                self.error_message = ""
                            else:
                                self.error_message = "Failed to read frame"
                        
                        # Schedule next snapshot
                        self.next_snapshot_time = datetime.now() + timedelta(
                            minutes=self.get_current_interval()
                        )
                    
                    except Exception as e:
                        self.error_message = f"Capture error: {str(e)[:25]}"
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.error_message = f"Thread error: {str(e)[:25]}"
                time.sleep(1)

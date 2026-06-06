"""Interview ream - Audio capture and volume monitoring (transcription coming next)."""

import threading
import queue

from reams.base import BaseRea
from utils.file_handler import FileHandler


class InterviewRea(BaseRea):
    """Interview ream for audio capture and monitoring."""
    
    def __init__(self, file_handler: FileHandler):
        """Initialize interview ream.
        
        Args:
            file_handler: FileHandler instance for file operations
        """
        super().__init__(file_handler, "interview", "Interview")
        self.is_recording = False
        self.audio_thread = None
        self.current_volume = 0  # RMS level (0-1)
        self.audio_enabled = False
        self.error_message = ""
    
    def start_session(self) -> None:
        """Start a new interview session (audio capture)."""
        super().start_session()
        self.is_recording = True
        self.current_volume = 0
        self.error_message = ""
        
        try:
            import sounddevice
            self.audio_enabled = True
        except ImportError:
            self.error_message = "Error: sounddevice not installed"
            self.is_recording = False
            return
        
        # Start audio capture thread
        self.audio_thread = threading.Thread(target=self._audio_capture_worker, daemon=True)
        self.audio_thread.start()
    
    def end_session(self) -> None:
        """End the current interview session."""
        self.is_recording = False
        super().end_session()
    
    def handle_input(self, input_data: str) -> None:
        """Handle text input (not used for interview).
        
        Args:
            input_data: Text input from user
        """
        pass
    
    def get_help_text(self) -> str:
        """Get help text for interview ream.
        
        Returns:
            Help text
        """
        return "Interview | Recording... | Ctrl+I: Stop | ↑↓: Scroll"
    
    def get_current_volume(self) -> float:
        """Get current audio volume level.
        
        Returns:
            Volume as float 0-1
        """
        return self.current_volume
    
    def _audio_capture_worker(self) -> None:
        """Background thread: capture audio and measure volume."""
        try:
            import sounddevice as sd
            import numpy as np
        except ImportError as e:
            self.error_message = f"Missing: {str(e)[:25]}"
            self.is_recording = False
            return
        
        # List available devices and find USB device
        usb_device_id = None
        try:
            devices = sd.query_devices()
            
            # Log device info for debugging
            if isinstance(devices, list):
                for idx, device in enumerate(devices):
                    if isinstance(device, dict) and 'name' in device:
                        if 'USB' in device['name'] or 'usb' in device['name']:
                            usb_device_id = idx
                            break
            
            # If no explicit USB device, try default input
            if usb_device_id is None:
                usb_device_id = sd.default.device[0]  # Use default input device
            
            self.error_message = f"Using device: {usb_device_id}"
        except Exception as e:
            self.error_message = f"Device: {str(e)[:25]}"
            self.is_recording = False
            return
        
        sample_rate = 16000
        chunk_duration = 0.5  # Process 0.5-second chunks for faster volume updates
        chunk_size = int(sample_rate * chunk_duration)
        
        try:
            # Create stream and use it properly
            stream = sd.InputStream(device=usb_device_id, samplerate=sample_rate, channels=1, blocksize=chunk_size, dtype='float32')
            stream.start()
            
            while self.is_recording:
                try:
                    # Read audio chunk from the stream
                    audio_chunk, _ = stream.read(frames=chunk_size)
                    
                    if len(audio_chunk) > 0:
                        # Calculate RMS (volume level)
                        rms = np.sqrt(np.mean(audio_chunk ** 2))
                        self.current_volume = float(rms)
                except:
                    pass
            
            stream.stop()
            stream.close()
        except Exception as e:
            self.error_message = f"Audio: {str(e)[:25]}"

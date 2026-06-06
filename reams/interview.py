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
        self.device_info = ""  # Debug info about audio device
    
    def start_session(self) -> None:
        """Start a new interview session (audio capture)."""
        super().start_session()
        self.is_recording = True
        self.current_volume = 0
        self.error_message = ""
        self.device_info = ""
        
        try:
            import sounddevice as sd
            self.audio_enabled = True
        except ImportError:
            self.error_message = "Missing: sounddevice"
            self.is_recording = False
            return
        
        # List all devices immediately
        try:
            devices = sd.query_devices()
            device_list = []
            
            if isinstance(devices, list):
                for idx, device in enumerate(devices):
                    if isinstance(device, dict):
                        name = device.get('name', 'Unknown')
                        max_in = device.get('max_input_channels', 0)
                        if max_in > 0:
                            device_list.append(f"{idx}:{name}")
            
            if device_list:
                self.device_info = "Devices: " + " | ".join(device_list)
            else:
                self.error_message = "No input devices found"
                self.is_recording = False
                return
        except Exception as e:
            self.error_message = f"Device list error: {str(e)[:20]}"
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
            self.error_message = f"Missing: {str(e)[:20]}"
            self.is_recording = False
            return
        
        # Use default input device
        try:
            usb_device_id = sd.default.device[0]
        except Exception as e:
            self.error_message = f"No default device: {str(e)[:20]}"
            self.is_recording = False
            return
        
        sample_rate = 16000
        chunk_duration = 0.5
        chunk_size = int(sample_rate * chunk_duration)
        
        try:
            # Create and start stream
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
            self.error_message = f"Audio error: {str(e)[:20]}"

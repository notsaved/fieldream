"""Interview ream - Audio capture and speech-to-text transcription."""

import threading
import queue

from reams.base import BaseRea
from utils.file_handler import FileHandler


class InterviewRea(BaseRea):
    """Interview ream for audio capture and transcription."""
    
    def __init__(self, file_handler: FileHandler):
        """Initialize interview ream.
        
        Args:
            file_handler: FileHandler instance for file operations
        """
        super().__init__(file_handler, "interview", "Interview")
        self.is_recording = False
        self.audio_thread = None
        self.transcription_thread = None
        self.current_volume = 0  # RMS level (0-1)
        self.error_message = ""
        self.device_info = ""
        self.selected_device = None
        self.audio_queue = queue.Queue()
        self.whisper_model = None
        self.last_transcription = ""
        self.chunks_processed = 0  # For debugging
    
    def start_session(self) -> None:
        """Start a new interview session (audio capture)."""
        super().start_session()
        self.is_recording = True
        self.current_volume = 0
        self.error_message = ""
        self.device_info = ""
        self.last_transcription = ""
        
        try:
            import sounddevice as sd
            import numpy as np
        except ImportError as e:
            self.error_message = f"Missing: {str(e)[:20]}"
            self.is_recording = False
            return
        
        # Find first available input device
        try:
            devices = sd.query_devices()
            usb_device_id = None
            
            # Look for USB device first
            if isinstance(devices, list):
                for idx, device in enumerate(devices):
                    if isinstance(device, dict):
                        name = device.get('name', '').lower()
                        max_in = device.get('max_input_channels', 0)
                        if max_in > 0 and ('usb' in name or 'webcam' in name):
                            usb_device_id = idx
                            break
            
            # If no USB device found, use the first device with input channels
            if usb_device_id is None and isinstance(devices, list):
                for idx, device in enumerate(devices):
                    if isinstance(device, dict):
                        max_in = device.get('max_input_channels', 0)
                        if max_in > 0:
                            usb_device_id = idx
                            break
            
            # Final fallback to default device
            if usb_device_id is None:
                usb_device_id = sd.default.device[0]
            
            # Get device name for display
            if isinstance(devices, list) and usb_device_id < len(devices):
                dev_name = devices[usb_device_id].get('name', 'Unknown') if isinstance(devices[usb_device_id], dict) else 'Unknown'
            else:
                dev_name = 'Default'
            
            self.device_info = f"Dev:{usb_device_id}({dev_name})"
            self.selected_device = usb_device_id
            
        except Exception as e:
            self.error_message = f"Device error: {str(e)[:20]}"
            self.is_recording = False
            return
        
        # Load Whisper model
        try:
            from faster_whisper import WhisperModel
            self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
            self.device_info += " | Model loaded"
        except ImportError:
            self.error_message = "Missing: faster-whisper"
            self.is_recording = False
            return
        except Exception as e:
            self.error_message = f"Model error: {str(e)[:25]}"
            self.is_recording = False
            return
        
        # Start audio and transcription threads
        self.audio_thread = threading.Thread(target=self._audio_capture_worker, daemon=True)
        self.audio_thread.start()
        
        self.transcription_thread = threading.Thread(target=self._transcription_worker, daemon=True)
        self.transcription_thread.start()
    
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
        """Background thread: capture audio and queue for transcription."""
        try:
            import sounddevice as sd
            import numpy as np
        except ImportError as e:
            self.error_message = f"Missing: {str(e)[:20]}"
            self.is_recording = False
            return
        
        device_id = self.selected_device
        if device_id is None:
            self.error_message = "No audio device selected"
            self.is_recording = False
            return
        
        sample_rate = 16000
        chunk_duration = 1  # 1-second chunks for transcription
        chunk_size = int(sample_rate * chunk_duration)
        
        try:
            stream = sd.InputStream(device=device_id, samplerate=sample_rate, channels=1, blocksize=chunk_size, dtype='float32')
            stream.start()
            
            while self.is_recording:
                try:
                    audio_chunk, _ = stream.read(frames=chunk_size)
                    
                    if len(audio_chunk) > 0:
                        # Calculate RMS for volume meter
                        rms = np.sqrt(np.mean(audio_chunk ** 2))
                        self.current_volume = float(rms)
                        
                        # Queue audio for transcription
                        self.audio_queue.put(audio_chunk)
                except:
                    pass
            
            stream.stop()
            stream.close()
        except Exception as e:
            self.error_message = f"Audio: {str(e)[:20]}"
    
    def _transcription_worker(self) -> None:
        """Background thread: transcribe audio chunks."""
        if self.whisper_model is None:
            self.error_message = "Model not loaded"
            return
        
        while self.is_recording or not self.audio_queue.empty():
            try:
                # Get audio chunk with timeout
                audio_chunk = self.audio_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            try:
                # Transcribe audio chunk
                segments, info = self.whisper_model.transcribe(audio_chunk, language="en")
                
                text_found = False
                for segment in segments:
                    text = segment.text.strip()
                    if text:
                        # Save to file
                        self.save_entry(text)
                        self.last_transcription = text
                        text_found = True
                
                if not text_found:
                    self.last_transcription = "[silence]"
                    
            except Exception as e:
                self.error_message = f"Transcribe error: {str(e)[:25]}"

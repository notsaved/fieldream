"""Interview ream - Speech-to-text transcription with speaker detection."""

import threading
import queue
import numpy as np
from faster_whisper import WhisperModel
from reams.base import BaseRea
from utils.file_handler import FileHandler


class SpeakerDetector:
    """Simple speaker detection using silence/activity patterns."""
    
    def __init__(self, sample_rate=16000, silence_threshold=0.02, min_silence_duration=0.5):
        """Initialize speaker detector.
        
        Args:
            sample_rate: Audio sample rate in Hz
            silence_threshold: RMS threshold below which audio is considered silence
            min_silence_duration: Seconds of silence needed to detect speaker change
        """
        self.sample_rate = sample_rate
        self.silence_threshold = silence_threshold
        self.min_silence_duration = min_silence_duration
        self.silence_duration = 0
        self.current_speaker = 1
        self.last_speaker = 0
    
    def detect(self, audio_chunk: np.ndarray) -> tuple:
        """Detect if speaker changed.
        
        Args:
            audio_chunk: Audio data as numpy array
            
        Returns:
            Tuple of (is_speech, speaker_id, speaker_changed)
        """
        # Calculate RMS (volume)
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        chunk_duration = len(audio_chunk) / self.sample_rate
        
        if rms < self.silence_threshold:
            # Silence detected
            self.silence_duration += chunk_duration
        else:
            # Speech detected
            self.silence_duration = 0
        
        speaker_changed = False
        if self.silence_duration >= self.min_silence_duration:
            # Long silence = speaker change
            if self.current_speaker == self.last_speaker:
                self.current_speaker = 3 - self.current_speaker  # Toggle 1 <-> 2
                self.last_speaker = self.current_speaker
                speaker_changed = True
            self.silence_duration = 0
        
        is_speech = rms >= self.silence_threshold
        return is_speech, self.current_speaker, speaker_changed


class InterviewRea(BaseRea):
    """Interview ream for speech-to-text transcription."""
    
    def __init__(self, file_handler: FileHandler):
        """Initialize interview ream.
        
        Args:
            file_handler: FileHandler instance for file operations
        """
        super().__init__(file_handler, "interview", "Interview")
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.transcription_thread = None
        self.whisper_model = None
        self.speaker_detector = None
        self.current_speaker = 1
        self.last_transcription = ""
    
    def start_session(self) -> None:
        """Start a new interview session."""
        super().start_session()
        self.is_recording = True
        self.current_speaker = 1
        
        # Initialize Whisper model (base is good for Pi)
        if self.whisper_model is None:
            self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        
        # Initialize speaker detector
        self.speaker_detector = SpeakerDetector()
        
        # Start transcription thread
        self.transcription_thread = threading.Thread(target=self._transcription_worker, daemon=True)
        self.transcription_thread.start()
        
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
        return "Interview | Recording... | Ctrl+O: Stop | ↑↓: Scroll"
    
    def _audio_capture_worker(self) -> None:
        """Background thread: capture audio from microphone."""
        try:
            import sounddevice as sd
        except ImportError:
            self.last_transcription = "Error: sounddevice not installed"
            return
        
        sample_rate = 16000
        chunk_duration = 2  # Process 2-second chunks
        chunk_size = sample_rate * chunk_duration
        
        try:
            with sd.InputStream(samplerate=sample_rate, channels=1, blocksize=chunk_size):
                while self.is_recording:
                    # Read audio chunk
                    audio_chunk, _ = sd.read(frames=chunk_size, dtype='float32')
                    
                    if len(audio_chunk) > 0:
                        self.audio_queue.put(audio_chunk)
        except Exception as e:
            self.last_transcription = f"Error: {str(e)}"
    
    def _transcription_worker(self) -> None:
        """Background thread: transcribe audio chunks."""
        while self.is_recording or not self.audio_queue.empty():
            try:
                # Get audio chunk with timeout
                audio_chunk = self.audio_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            try:
                # Detect speaker
                is_speech, speaker_id, speaker_changed = self.speaker_detector.detect(audio_chunk)
                
                if is_speech:
                    # Transcribe
                    segments, info = self.whisper_model.transcribe(audio_chunk, language="en")
                    
                    for segment in segments:
                        text = segment.text.strip()
                        if text:
                            # Add speaker label if changed
                            if speaker_changed or speaker_id != self.current_speaker:
                                self.current_speaker = speaker_id
                                speaker_prefix = f"\n**[Speaker {speaker_id}]**\n"
                            else:
                                speaker_prefix = " "
                            
                            # Save to file
                            entry = speaker_prefix + text
                            self.save_entry(entry)
                            self.last_transcription = text
            
            except Exception as e:
                self.last_transcription = f"Transcription error: {str(e)}"

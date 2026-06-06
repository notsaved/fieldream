"""Observation ream - Text-based note taking."""

from reams.base import BaseRea
from utils.file_handler import FileHandler


class ObservationRea(BaseRea):
    """Observation ream for typing and appending text notes."""

    def __init__(self, file_handler: FileHandler):
        """Initialize observation ream.
        
        Args:
            file_handler: FileHandler instance for file operations
        """
        super().__init__(file_handler, "observation", "Observation")

    def append_note(self, text: str) -> None:
        """Append a note entry to the observation file.
        
        Args:
            text: The note text to append
        """
        self.save_entry(text)
        self.current_buffer = ""

    def get_help_text(self) -> str:
        """Get help text for observation ream.
        
        Returns:
            Help text with available commands
        """
        return "Observation | Ctrl+S: Save | Ctrl+C: Clear | Ctrl+N: New | Ctrl+Q: Quit"

    def clear_buffer(self) -> None:
        """Clear the current input buffer without saving."""
        self.current_buffer = ""

    def get_current_text(self) -> str:
        """Get the current buffer text.
        
        Returns:
            Current buffer content
        """
        return self.current_buffer

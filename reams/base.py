"""Base class for all reams (note-taking modes)."""

from abc import ABC, abstractmethod
from pathlib import Path
from utils.file_handler import FileHandler


class BaseRea(ABC):
    """Abstract base class for ream implementations."""

    def __init__(self, file_handler: FileHandler, prefix: str, name: str):
        """Initialize a ream.
        
        Args:
            file_handler: FileHandler instance for file operations
            prefix: The ream prefix (e.g., 'observation')
            name: Display name of the ream
        """
        self.file_handler = file_handler
        self.prefix = prefix
        self.name = name
        self.current_file = None
        self.session_started = False

    def start_session(self) -> None:
        """Start a new session for this ream."""
        self.current_file = self.file_handler.get_session_file(self.prefix)
        self.file_handler.init_session_file(
            self.current_file, self.name, self.prefix
        )
        self.session_started = True

    def end_session(self) -> None:
        """End the current session."""
        self.session_started = False

    @abstractmethod
    def handle_input(self, input_data: str) -> None:
        """Handle input data for this ream.
        
        Args:
            input_data: Data to process
        """
        pass

    @abstractmethod
    def get_help_text(self) -> str:
        """Get help text for this ream.
        
        Returns:
            Help text describing available commands
        """
        pass

    def save_entry(self, content: str) -> Path:
        """Save an entry to the current session file.
        
        Args:
            content: Content to save
            
        Returns:
            Path to the saved file
        """
        if not self.session_started:
            self.start_session()
        
        self.file_handler.append_to_file(self.current_file, content)
        return self.current_file

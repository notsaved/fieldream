"""File handling utilities for managing markdown notes."""

from datetime import datetime
from pathlib import Path


class FileHandler:
    """Handles reading and writing markdown note files."""

    def __init__(self, notes_dir, session_folder: Path):
        """Initialize file handler.
        
        Args:
            notes_dir: Unused (kept for compatibility)
            session_folder: Path to the current session folder
        """
        self.session_folder = session_folder

    def get_session_file(self, prefix: str) -> Path:
        """Get or create today's session file for a ream.
        
        Args:
            prefix: The ream prefix (e.g., 'observation', 'interview')
            
        Returns:
            Path to the session markdown file
        """
        if self.session_folder is None:
            raise ValueError("Session folder not set")
        
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{prefix}_{today}.md"
        filepath = self.session_folder / filename
        return filepath

    def append_to_file(self, filepath: Path, content: str) -> None:
        """Append content to a markdown file.
        
        Args:
            filepath: Path to the markdown file
            content: Content to append
        """
        # Add timestamp and separator
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"\n**[{timestamp}]**\n{content}\n"
        
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(entry)

    def create_header(self, title: str, prefix: str) -> str:
        """Create a markdown header for a new session file.
        
        Args:
            title: Title for the session
            prefix: The ream prefix
            
        Returns:
            Formatted markdown header
        """
        date = datetime.now().strftime("%Y-%m-%d")
        time = datetime.now().strftime("%H:%M:%S")
        
        header = f"""# {title}
**Date:** {date}  
**Started:** {time}

"""
        return header

    def init_session_file(self, filepath: Path, title: str, prefix: str) -> None:
        """Initialize a new session file if it doesn't exist.
        
        Args:
            filepath: Path to the session file
            title: Title for the session
            prefix: The ream prefix
        """
        if not filepath.exists():
            header = self.create_header(title, prefix)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(header)

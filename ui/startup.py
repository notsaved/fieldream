"""Startup screen for session creation."""

import curses
from datetime import datetime
from pathlib import Path


class StartupScreen:
    """Handles session name input and creation."""

    def __init__(self, stdscr, notes_dir: Path):
        """Initialize startup screen.
        
        Args:
            stdscr: Curses standard screen object
            notes_dir: Path to notes directory
        """
        self.stdscr = stdscr
        self.notes_dir = notes_dir
        self.height, self.width = stdscr.getmaxyx()

    def prompt_session_name(self) -> Path:
        """Prompt user for session name and create session folder.
        
        Returns:
            Path to the created session folder
        """
        self.stdscr.clear()
        
        # Draw title
        title = "Fieldream - New Session"
        self.stdscr.addstr(2, (self.width - len(title)) // 2, title, curses.A_BOLD)
        
        # Draw prompt
        prompt = "Enter session name (or press Ctrl+C to cancel):"
        self.stdscr.addstr(5, 2, prompt)
        
        # Input field
        self.stdscr.addstr(7, 2, "Session name: ")
        curses.curs_set(1)
        self.stdscr.refresh()
        
        # Get input
        input_str = ""
        while True:
            ch = self.stdscr.getch()
            
            if ch == 27:  # ESC
                raise KeyboardInterrupt()
            elif ch == 3:  # Ctrl+C
                raise KeyboardInterrupt()
            elif ch == curses.KEY_BACKSPACE or ch == 127:
                if input_str:
                    input_str = input_str[:-1]
            elif ch == ord('\n'):
                if input_str.strip():
                    break
            elif 32 <= ch <= 126:  # Printable characters
                if len(input_str) < 50:
                    input_str += chr(ch)
            
            # Redraw input field
            self.stdscr.addstr(7, 16, " " * 50)
            self.stdscr.addstr(7, 16, input_str)
            self.stdscr.refresh()
        
        curses.curs_set(0)
        
        # Create session folder with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_name = f"{input_str}_{timestamp}"
        session_folder = self.notes_dir / session_name
        session_folder.mkdir(parents=True, exist_ok=True)
        
        return session_folder, session_name

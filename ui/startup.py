"""Startup screen for session creation."""

import curses
from datetime import datetime
from pathlib import Path


class StartupScreen:
    """Handles session name input and creation."""

    def __init__(self, stdscr, default_notes_dir: Path):
        """Initialize startup screen.
        
        Args:
            stdscr: Curses standard screen object
            default_notes_dir: Default path for notes directory
        """
        self.stdscr = stdscr
        self.default_notes_dir = default_notes_dir
        self.height, self.width = stdscr.getmaxyx()

    def prompt_session_name(self) -> tuple:
        """Prompt user for session name.
        
        Returns:
            Tuple of (session_name, session_folder_path)
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
        
        session_name = input_str.strip()
        
        # Now prompt for save location
        save_location = self._prompt_save_location()
        
        curses.curs_set(0)
        
        # Create session folder with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"{session_name}_{timestamp}"
        session_folder = save_location / folder_name
        session_folder.mkdir(parents=True, exist_ok=True)
        
        return session_folder, folder_name

    def _prompt_save_location(self) -> Path:
        """Prompt user for save location.
        
        Returns:
            Path to save location
        """
        self.stdscr.clear()
        
        title = "Fieldream - Save Location"
        self.stdscr.addstr(2, (self.width - len(title)) // 2, title, curses.A_BOLD)
        
        options = [
            ("D", "Desktop", self._get_desktop_dir()),
            ("H", "Home", Path.home()),
            ("C", "Custom path", None),
        ]
        
        self.stdscr.addstr(5, 2, "Where to save session?")
        self.stdscr.addstr(7, 2, "(Press D, H, or C)")
        
        for i, (key, label, path) in enumerate(options):
            path_str = str(path) if path else ""
            line = f"  [{key}] {label:<15} {path_str[:40]}"
            self.stdscr.addstr(9 + i * 2, 4, line)
        
        self.stdscr.refresh()
        
        while True:
            ch = self.stdscr.getch()
            
            if ch == ord('D') or ch == ord('d'):
                return self._get_desktop_dir()
            elif ch == ord('H') or ch == ord('h'):
                return Path.home()
            elif ch == ord('C') or ch == ord('c'):
                return self._prompt_custom_path()
            elif ch == 3:  # Ctrl+C
                raise KeyboardInterrupt()

    def _get_desktop_dir(self) -> Path:
        """Get desktop directory, fallback to home if doesn't exist.
        
        Returns:
            Path to desktop or home
        """
        desktop = Path.home() / "Desktop"
        if desktop.exists():
            return desktop
        return Path.home()

    def _prompt_custom_path(self) -> Path:
        """Prompt user for custom save path.
        
        Returns:
            Path to custom location
        """
        self.stdscr.clear()
        
        title = "Fieldream - Custom Path"
        self.stdscr.addstr(2, (self.width - len(title)) // 2, title, curses.A_BOLD)
        
        self.stdscr.addstr(5, 2, "Enter full path (e.g., /home/user/fieldream):")
        self.stdscr.addstr(7, 2, "Path: ")
        
        curses.curs_set(1)
        self.stdscr.refresh()
        
        input_str = ""
        while True:
            ch = self.stdscr.getch()
            
            if ch == 27:  # ESC - Back to location menu
                return self._prompt_save_location()
            elif ch == 3:  # Ctrl+C
                raise KeyboardInterrupt()
            elif ch == curses.KEY_BACKSPACE or ch == 127:
                if input_str:
                    input_str = input_str[:-1]
            elif ch == ord('\n'):
                path = Path(input_str.strip())
                if path.parent.exists():
                    return path
                else:
                    self.stdscr.addstr(9, 2, "Path parent doesn't exist! Press any key to retry...")
                    self.stdscr.refresh()
                    self.stdscr.getch()
                    input_str = ""
                    self.stdscr.addstr(7, 8, " " * 60)
                    self.stdscr.refresh()
            elif 32 <= ch <= 126:  # Printable characters
                if len(input_str) < 80:
                    input_str += chr(ch)
            
            # Redraw input field
            self.stdscr.addstr(7, 8, " " * 70)
            self.stdscr.addstr(7, 8, input_str)
            self.stdscr.refresh()
        
        curses.curs_set(0)

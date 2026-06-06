"""Startup screen for session creation."""

import curses
from datetime import datetime
from pathlib import Path


class StartupScreen:
    """Handles session name input and creation."""

    def __init__(self, stdscr, app_base_dir: Path):
        """Initialize startup screen.
        
        Args:
            stdscr: Curses standard screen object
            app_base_dir: Base application directory
        """
        self.stdscr = stdscr
        self.app_base_dir = app_base_dir
        self.height, self.width = stdscr.getmaxyx()

    def prompt_session_name(self) -> tuple:
        """Prompt user for session name.
        
        Returns:
            Tuple of (session_folder, session_name) or (None, None) if cancelled
        """
        try:
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
            if not session_name:
                return (None, None)
            
            # Now prompt for save location
            save_location = self._prompt_save_location()
            if save_location is None:
                return (None, None)
            
            curses.curs_set(0)
            
            # Create session folder with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            folder_name = f"{session_name}_{timestamp}"
            session_folder = save_location / folder_name
            session_folder.mkdir(parents=True, exist_ok=True)
            
            return (session_folder, folder_name)
        
        except KeyboardInterrupt:
            curses.curs_set(0)
            return (None, None)
        except Exception as e:
            curses.curs_set(0)
            return (None, None)

    def _prompt_save_location(self) -> Path:
        """Prompt user for save location.
        
        Returns:
            Path to save location or None if cancelled
        """
        try:
            self.stdscr.clear()
            
            title = "Fieldream - Save Location"
            self.stdscr.addstr(2, (self.width - len(title)) // 2, title, curses.A_BOLD)
            
            desktop_dir = Path.home() / "Desktop"
            docs_dir = Path.home() / "Documents"
            root_dir = self.app_base_dir
            
            options = [
                ("R", "Root folder (repo)", root_dir),
                ("D", "Desktop", desktop_dir if desktop_dir.exists() else None),
                ("C", "Documents", docs_dir if docs_dir.exists() else None),
                ("T", "Target folder (custom path)", None),
            ]
            
            self.stdscr.addstr(5, 2, "Where to save session?")
            self.stdscr.addstr(7, 2, "(Press R, D, C, or T)")
            
            row = 9
            for key, label, path in options:
                if path is None and key != "T":
                    # Skip non-existent paths unless it's the custom option
                    continue
                
                path_str = str(path) if path else "[type path]"
                display = f"  [{key}] {label:<25} {path_str[:35]}"
                self.stdscr.addstr(row, 2, display)
                row += 2
            
            self.stdscr.refresh()
            
            while True:
                ch = self.stdscr.getch()
                
                if ch == ord('R') or ch == ord('r'):
                    return root_dir
                elif ch == ord('D') or ch == ord('d'):
                    if desktop_dir.exists():
                        return desktop_dir
                elif ch == ord('C') or ch == ord('c'):
                    if docs_dir.exists():
                        return docs_dir
                elif ch == ord('T') or ch == ord('t'):
                    result = self._prompt_custom_path()
                    if result:
                        return result
                    # If custom path returns None, show location menu again
                    self.stdscr.clear()
                    self.stdscr.addstr(2, (self.width - len(title)) // 2, title, curses.A_BOLD)
                    self.stdscr.addstr(5, 2, "Where to save session?")
                    self.stdscr.addstr(7, 2, "(Press R, D, C, or T)")
                    row = 9
                    for key, label, path in options:
                        if path is None and key != "T":
                            continue
                        path_str = str(path) if path else "[type path]"
                        display = f"  [{key}] {label:<25} {path_str[:35]}"
                        self.stdscr.addstr(row, 2, display)
                        row += 2
                    self.stdscr.refresh()
                elif ch == 3:  # Ctrl+C
                    raise KeyboardInterrupt()
        
        except KeyboardInterrupt:
            return None
        except Exception:
            return None

    def _prompt_custom_path(self) -> Path:
        """Prompt user for custom save path.
        
        Returns:
            Path to custom location or None if cancelled
        """
        try:
            self.stdscr.clear()
            
            title = "Fieldream - Custom Path"
            self.stdscr.addstr(2, (self.width - len(title)) // 2, title, curses.A_BOLD)
            
            self.stdscr.addstr(5, 2, "Enter full path (e.g., /home/user/mydata):")
            self.stdscr.addstr(7, 2, "Path: ")
            
            curses.curs_set(1)
            self.stdscr.refresh()
            
            input_str = ""
            while True:
                ch = self.stdscr.getch()
                
                if ch == 27:  # ESC - Cancel custom path
                    curses.curs_set(0)
                    return None
                elif ch == 3:  # Ctrl+C
                    raise KeyboardInterrupt()
                elif ch == curses.KEY_BACKSPACE or ch == 127:
                    if input_str:
                        input_str = input_str[:-1]
                elif ch == ord('\n'):
                    path = Path(input_str.strip())
                    if path.parent.exists() or path == path.parent or path.exists():
                        curses.curs_set(0)
                        return path
                    else:
                        self.stdscr.addstr(9, 2, "Parent path doesn't exist! Press ESC to go back")
                        self.stdscr.refresh()
                        self.stdscr.getch()
                        input_str = ""
                        self.stdscr.addstr(7, 8, " " * 70)
                        self.stdscr.addstr(9, 2, " " * 70)
                        self.stdscr.refresh()
                elif 32 <= ch <= 126:  # Printable characters
                    if len(input_str) < 80:
                        input_str += chr(ch)
                
                # Redraw input field
                self.stdscr.addstr(7, 8, " " * 70)
                self.stdscr.addstr(7, 8, input_str)
                self.stdscr.refresh()
            
            curses.curs_set(0)
        except KeyboardInterrupt:
            curses.curs_set(0)
            return None
        except Exception:
            curses.curs_set(0)
            return None

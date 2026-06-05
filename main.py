"""Main entry point for Fieldream note-taking system."""

import curses
import sys
from pathlib import Path

from config import NOTES_DIR, REAMS
from ui.window import WindowManager
from ui.startup import StartupScreen
from utils.file_handler import FileHandler
from reams.observation import ObservationRea


class Fieldream:
    """Main application class for Fieldream."""

    def __init__(self, stdscr):
        """Initialize Fieldream application.
        
        Args:
            stdscr: Curses standard screen object
        """
        self.stdscr = stdscr
        self.window_manager = WindowManager(stdscr)
        
        # Session setup
        self.session_folder = None
        self.session_name = None
        self.file_handler = None
        
        # Ream management
        self.reams = {}
        self.active_ream = None  # No ream active at start
        
        self.running = True
        self.status_message = "Ready"
        
        # Mode
        self.mode = "dashboard"  # "dashboard" or "editing"

    def init_session(self) -> bool:
        """Initialize a new session.
        
        Returns:
            True if successful, False if cancelled
        """
        try:
            startup = StartupScreen(self.stdscr, NOTES_DIR)
            self.session_folder, self.session_name = startup.prompt_session_name()
            self.file_handler = FileHandler(NOTES_DIR, self.session_folder)
            
            # Initialize reams with the session file handler
            self.reams = {
                "observation": ObservationRea(self.file_handler),
                # "interview": InterviewRea(self.file_handler),
                # "snapshot": SnapshotRea(self.file_handler),
            }
            
            self.status_message = f"Session created: {self.session_name}"
            return True
        except KeyboardInterrupt:
            return False

    def get_ream_statuses(self) -> list:
        """Get status of all reams.
        
        Returns:
            List of ream status dicts
        """
        statuses = []
        for ream_config in REAMS:
            key = ream_config["key"]
            status = {
                "key": key,
                "name": ream_config["name"],
                "shortcut": ream_config["shortcut"],
                "description": ream_config["description"],
                "active": self.active_ream == key,
            }
            statuses.append(status)
        return statuses

    def draw_dashboard(self) -> None:
        """Draw the dashboard view."""
        self.window_manager.draw_header("Fieldream", "Dashboard")
        self.window_manager.draw_dashboard(self.session_name, self.get_ream_statuses())
        self.window_manager.draw_footer("Ctrl+O: Observation | Ctrl+I: Interview | Ctrl+S: Snapshot | Ctrl+Q: Quit")
        self.window_manager.draw_status(self.status_message)
        self.window_manager.refresh_all()

    def handle_observation_mode(self) -> None:
        """Run the observation ream editing mode."""
        if "observation" not in self.reams:
            self.status_message = "Observation ream not initialized"
            return
        
        observation = self.reams["observation"]
        observation.start_session()
        
        content_win = self.window_manager.get_content_area()
        content_win.clear()
        self.window_manager.clear_content()
        
        # Draw header for editing mode
        self.window_manager.draw_header("Fieldream", "Observation Mode")
        self.window_manager.draw_footer("Ctrl+S: Save | Ctrl+C: Clear | Ctrl+N: New | Ctrl+Q: Back to Dashboard")
        
        y, x = 1, 0  # Start position
        
        self.window_manager.refresh_all()
        
        editing = True
        while editing and self.running:
            try:
                ch = self.stdscr.getch()
                
                if ch == 17:  # Ctrl+Q - Return to dashboard
                    current_text = observation.get_current_text()
                    if current_text.strip():
                        self.status_message = "Entry in progress (Ctrl+S to save)"
                    editing = False
                elif ch == 19:  # Ctrl+S - Save
                    current_text = observation.get_current_text()
                    if current_text.strip():
                        filepath = observation.append_note(current_text)
                        self.status_message = f"✓ Saved: {filepath.name}"
                        self.window_manager.clear_content()
                        y, x = 1, 0
                    else:
                        self.status_message = "Nothing to save"
                elif ch == 3:  # Ctrl+C - Clear buffer
                    observation.clear_buffer()
                    self.window_manager.clear_content()
                    y, x = 1, 0
                    self.status_message = "Buffer cleared"
                elif ch == 14:  # Ctrl+N - New entry (same as clear for observation)
                    observation.clear_buffer()
                    self.window_manager.clear_content()
                    y, x = 1, 0
                    self.status_message = "New entry started"
                elif ch == curses.KEY_BACKSPACE or ch == 127:  # Backspace
                    current_text = observation.get_current_text()
                    if current_text:
                        observation.current_buffer = current_text[:-1]
                        if x > 0:
                            x -= 1
                            content_win.delch(y, x)
                        elif y > 1:
                            y -= 1
                            x = self.window_manager.width - 1
                elif ch == curses.KEY_ENTER or ch == ord('\n'):  # Enter
                    observation.current_buffer += "\n"
                    content_win.addch(y, x, '\n')
                    y += 1
                    x = 0
                    if y >= self.window_manager.height - 3:
                        content_win.scroll(1)
                        y -= 1
                elif 32 <= ch <= 126:  # Printable characters
                    observation.current_buffer += chr(ch)
                    content_win.addch(y, x, ch)
                    x += 1
                    if x >= self.window_manager.width:
                        x = 0
                        y += 1
                        if y >= self.window_manager.height - 3:
                            content_win.scroll(1)
                            y -= 1
                
                # Update status dynamically
                char_count = len(observation.get_current_text())
                self.status_message = f"{char_count} characters"
                
                self.window_manager.draw_header("Fieldream", "Observation Mode")
                self.window_manager.draw_footer("Ctrl+S: Save | Ctrl+C: Clear | Ctrl+N: New | Ctrl+Q: Back to Dashboard")
                self.window_manager.draw_status(self.status_message)
                self.window_manager.refresh_all()
                
            except KeyboardInterrupt:
                editing = False
        
        observation.end_session()
        self.mode = "dashboard"

    def run(self) -> None:
        """Main application loop."""
        curses.curs_set(0)  # Hide cursor by default
        
        # Initialize session
        if not self.init_session():
            self.running = False
            return
        
        self.mode = "dashboard"
        
        while self.running:
            try:
                if self.mode == "dashboard":
                    self.draw_dashboard()
                    ch = self.stdscr.getch()
                    
                    if ch == 15:  # Ctrl+O - Observation
                        self.active_ream = "observation"
                        self.mode = "editing"
                        self.handle_observation_mode()
                        self.active_ream = None
                    elif ch == 9:  # Ctrl+I - Interview
                        self.status_message = "Interview ream not yet implemented"
                    elif ch == 19:  # Ctrl+S - Snapshot
                        self.status_message = "Snapshot ream not yet implemented"
                    elif ch == 17:  # Ctrl+Q - Quit
                        self.running = False
                    
            except Exception as e:
                self.status_message = f"Error: {str(e)}"
                self.window_manager.draw_status(self.status_message)
                self.window_manager.refresh_all()
                self.stdscr.getch()


def main(stdscr):
    """Main entry point for curses application.
    
    Args:
        stdscr: Curses standard screen object
    """
    # Configure curses
    stdscr.keypad(True)
    stdscr.nodelay(False)
    
    # Create and run application
    app = Fieldream(stdscr)
    try:
        app.run()
    except Exception as e:
        curses.endwin()
        print(f"Error: {e}")


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nFieldream closed")
        sys.exit(0)

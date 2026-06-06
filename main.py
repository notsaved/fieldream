"""Main entry point for Fieldream note-taking system."""

import curses
import sys
from pathlib import Path

from config import REAMS, BASE_DIR
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
        self.input_text = ""  # Current input in active ream
        
        # Scrolling
        self.scroll_offsets = {}  # Track scroll position for each ream
        
        self.running = True
        self.status_message = "Ready"

    def init_session(self) -> bool:
        """Initialize a new session.
        
        Returns:
            True if successful, False if cancelled
        """
        try:
            startup = StartupScreen(self.stdscr, BASE_DIR)
            result = startup.prompt_session_name()
            
            if result is None or len(result) != 2:
                self.status_message = "Session creation failed"
                return False
            
            self.session_folder, self.session_name = result
            
            if not self.session_folder or not self.session_name:
                self.status_message = "Invalid session folder or name"
                return False
            
            self.file_handler = FileHandler(None, self.session_folder)
            
            # Initialize reams with the session file handler
            self.reams = {
                "observation": ObservationRea(self.file_handler),
                # "interview": InterviewRea(self.file_handler),
                # "snapshot": SnapshotRea(self.file_handler),
            }
            
            # Initialize scroll offsets
            self.scroll_offsets = {key: 0 for key in self.reams.keys()}
            
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

    def get_ream_contents(self) -> dict:
        """Get current contents of all ream .md files.
        
        Returns:
            Dict mapping ream key to file contents
        """
        contents = {}
        for key, ream in self.reams.items():
            if ream.session_started and ream.current_file:
                try:
                    with open(ream.current_file, "r", encoding="utf-8") as f:
                        contents[key] = f.read()
                except:
                    contents[key] = ""
            else:
                contents[key] = ""
        return contents

    def toggle_ream(self, ream_key: str) -> None:
        """Toggle a ream on or off.
        
        Args:
            ream_key: The ream key to toggle
        """
        if self.active_ream == ream_key:
            # Deactivate
            self.active_ream = None
            self.input_text = ""
            self.status_message = f"Deactivated {ream_key}"
        else:
            # Activate
            if ream_key in self.reams:
                self.active_ream = ream_key
                self.input_text = ""
                if not self.reams[ream_key].session_started:
                    self.reams[ream_key].start_session()
                # Reset scroll to bottom when activating
                self.scroll_offsets[ream_key] = 0
                self.status_message = f"Activated {ream_key} - type and press Enter to save"
            else:
                self.status_message = f"{ream_key} ream not yet implemented"

    def save_active_entry(self) -> None:
        """Save the current input as an entry in the active ream."""
        if self.active_ream:
            text_to_save = self.input_text.strip()
            if text_to_save:
                ream = self.reams[self.active_ream]
                filepath = ream.append_note(text_to_save)
                self.status_message = f"✓ Saved: {len(text_to_save)} chars"
            else:
                self.status_message = "Entry empty - nothing saved"
            
            # Always clear the input field after Enter
            self.input_text = ""

    def draw_dashboard(self) -> None:
        """Draw the dashboard view."""
        self.window_manager.draw_header("Fieldream", "Dashboard")
        
        ream_contents = self.get_ream_contents()
        
        self.window_manager.draw_dashboard(
            self.session_name, 
            self.get_ream_statuses(),
            ream_contents=ream_contents,
            input_text=self.input_text,
            active_ream=self.active_ream,
            scroll_offsets=self.scroll_offsets
        )
        
        if self.active_ream:
            footer_text = f"[{self.active_ream.upper()}] Type and press Enter | ↑↓: Scroll | Ctrl+Q: Deactivate"
        else:
            footer_text = "Ctrl+O: Observation | Ctrl+I: Interview | Ctrl+S: Snapshot | ↑↓: Scroll | Ctrl+Q: Quit"
        
        self.window_manager.draw_footer(footer_text)
        self.window_manager.draw_status(self.status_message)
        self.window_manager.refresh_all()

    def run(self) -> None:
        """Main application loop."""
        import time
        curses.curs_set(0)  # Hide cursor by default
        
        # Initialize session
        if not self.init_session():
            self.running = False
            return
        
        self.stdscr.nodelay(True)  # Non-blocking input
        
        while self.running:
            try:
                # Add small delay to prevent rapid flashing
                time.sleep(0.05)
                
                self.draw_dashboard()
                
                ch = self.stdscr.getch()
                
                if ch == -1:
                    # No input available
                    continue
                
                # Show key code in status
                self.status_message = f"Key: {ch}"
                
                # Handle scrolling (available in any mode)
                if ch == curses.KEY_UP:
                    if self.active_ream and self.active_ream in self.scroll_offsets:
                        self.scroll_offsets[self.active_ream] = max(0, self.scroll_offsets[self.active_ream] - 3)
                    continue
                elif ch == curses.KEY_DOWN:
                    if self.active_ream and self.active_ream in self.scroll_offsets:
                        self.scroll_offsets[self.active_ream] += 3
                    continue
                
                if self.active_ream:
                    # Handle input for active ream
                    if ch == 17:  # Ctrl+Q - Deactivate current ream
                        if self.input_text.strip():
                            self.status_message = "Entry in progress (press Enter to save, or Ctrl+Q to discard)"
                        else:
                            self.toggle_ream(self.active_ream)
                    elif ch == curses.KEY_ENTER or ch == ord('\n'):  # Enter - Save
                        self.save_active_entry()
                    elif ch == curses.KEY_BACKSPACE or ch == 127:  # Backspace
                        if self.input_text:
                            self.input_text = self.input_text[:-1]
                    elif 32 <= ch <= 126:  # Printable characters
                        self.input_text += chr(ch)
                else:
                    # Handle dashboard navigation
                    if ch == 15:  # Ctrl+O - Toggle Observation
                        self.toggle_ream("observation")
                    elif ch == 9:  # Ctrl+I - Toggle Interview
                        self.toggle_ream("interview")
                    elif ch == 19:  # Ctrl+S - Toggle Snapshot
                        self.toggle_ream("snapshot")
                    elif ch == 17:  # Ctrl+Q - Quit
                        self.running = False
                
            except Exception as e:
                self.status_message = f"Error: {str(e)[:40]}"
                self.window_manager.draw_status(self.status_message)
                self.window_manager.refresh_all()
                time.sleep(0.1)


def main(stdscr):
    """Main entry point for curses application.
    
    Args:
        stdscr: Curses standard screen object
    """
    # Configure curses
    stdscr.keypad(True)
    
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

"""Main entry point for Fieldream note-taking system."""

import curses
import sys
from pathlib import Path

from config import REAMS, BASE_DIR
from ui.window import WindowManager
from ui.startup import StartupScreen
from utils.file_handler import FileHandler
from reams.observation import ObservationRea

# Try to import interview, but don't fail if audio libs missing
try:
    from reams.interview import InterviewRea
    HAS_INTERVIEW = True
except ImportError:
    HAS_INTERVIEW = False
    InterviewRea = None

# Try to import snapshot, but don't fail if vision libs missing
try:
    from reams.snapshot import SnapshotRea
    HAS_SNAPSHOT = True
except ImportError:
    HAS_SNAPSHOT = False
    SnapshotRea = None


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
        self.active_reams = {"observation"}  # Observation always active
        self.input_text = ""  # Current input in observation ream
        
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
            }
            
            # Add interview if available
            if HAS_INTERVIEW and InterviewRea:
                self.reams["interview"] = InterviewRea(self.file_handler)
            
            # Add snapshot if available
            if HAS_SNAPSHOT and SnapshotRea:
                self.reams["snapshot"] = SnapshotRea(self.file_handler)
            
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
                "active": key in self.active_reams,
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
        """Toggle a ream on or off (Observation cannot be toggled).
        
        Args:
            ream_key: The ream key to toggle
        """
        from debug import log
        log(f"toggle_ream: called with {ream_key}")
        
        if ream_key == "observation":
            log("toggle_ream: observation always active")
            return  # Observation is always active
        
        if ream_key in self.active_reams:
            # Deactivate
            log(f"toggle_ream: deactivating {ream_key}")
            self.active_reams.remove(ream_key)
            if ream_key in self.reams and self.reams[ream_key].session_started:
                try:
                    log(f"toggle_ream: calling end_session for {ream_key}")
                    self.reams[ream_key].end_session()
                    log(f"toggle_ream: end_session done for {ream_key}")
                except Exception as e:
                    log(f"toggle_ream: error ending session: {e}")
            self.status_message = f"Deactivated {ream_key}"
            log(f"toggle_ream: {ream_key} deactivated")
        else:
            # Activate
            log(f"toggle_ream: activating {ream_key}")
            if ream_key in self.reams:
                self.active_reams.add(ream_key)
                log(f"toggle_ream: added {ream_key} to active_reams")
                if not self.reams[ream_key].session_started:
                    try:
                        log(f"toggle_ream: calling start_session for {ream_key}")
                        self.reams[ream_key].start_session()
                        log(f"toggle_ream: start_session done for {ream_key}")
                    except Exception as e:
                        log(f"toggle_ream: error starting session: {e}")
                        self.status_message = f"Error: {str(e)[:30]}"
                self.status_message = f"Activated {ream_key}"
                log(f"toggle_ream: {ream_key} activated")
            else:
                self.status_message = f"{ream_key} ream not yet implemented"
                log(f"toggle_ream: {ream_key} not in reams")
        log(f"toggle_ream: finished with {ream_key}")

    def count_words(self, text: str) -> int:
        """Count words in text.
        
        Args:
            text: Text to count words in
            
        Returns:
            Number of words
        """
        return len(text.split())
    
    def render_volume_meter(self, volume: float, max_width: int = 10) -> str:
        """Render a volume meter visualization.
        
        Args:
            volume: Volume level 0-1
            max_width: Width of the meter in characters
            
        Returns:
            String like "[████░░░░]"
        """
        filled = int(volume * max_width)
        empty = max_width - filled
        meter = "[" + "█" * filled + "░" * empty + "]"
        
        # Convert volume to dB (0-1 -> -40 to 0 dB approximately)
        db = max(-40, int(20 * (volume - 1)) if volume > 0 else -40)
        
        return f"{meter} {db}dB"
    
    def save_active_entry(self) -> None:
        """Save the current input as an entry in the observation ream."""
        # Only Observation supports text input
        ream = self.reams.get("observation")
        if not ream:
            self.status_message = "Observation ream not available"
            return
        
        text_to_save = self.input_text.strip()
        if text_to_save:
            filepath = ream.append_note(text_to_save)
            char_count = len(text_to_save)
            word_count = self.count_words(text_to_save)
            self.status_message = f"✓ Saved: {char_count}/{word_count}"
        else:
            self.status_message = "Entry empty - nothing saved"
        
        # Always clear the input field after Enter
        self.input_text = ""

    def draw_dashboard(self) -> None:
        """Draw the dashboard view."""
        from debug import log
        try:
            log("draw_dashboard: start")
            self.window_manager.draw_header("Fieldream", "Dashboard")
            
            ream_contents = self.get_ream_contents()
            log("draw_dashboard: got contents")
            
            self.window_manager.draw_dashboard(
                self.session_name, 
                self.get_ream_statuses(),
                ream_contents=ream_contents,
                input_text=self.input_text,
                scroll_offsets=self.scroll_offsets
            )
            log("draw_dashboard: dashboard drawn")
            
            # Footer text shows keyboard shortcuts
            footer_text = "Ctrl+I: Interview | Ctrl+S: Snapshot | Ctrl+P: Capture | ↑↓: Interval"
            
            # Prepare status bar data
            volume = 0
            transcription_status = ""
            queue_size = 0
            processing_time = 0.0
            interview_active = False
            
            # Snapshot status
            snapshot_interval = 0
            snapshot_countdown = 0
            snapshot_active = False
            
            if "interview" in self.active_reams and "interview" in self.reams:
                ream = self.reams["interview"]
                interview_active = True
                # Show error if present
                if ream.error_message:
                    transcription_status = f"Error: {ream.error_message[:20]}"
                else:
                    volume = ream.get_current_volume()
                    transcription_status = ream.transcription_status
                    queue_size = ream.audio_queue.qsize()
                    processing_time = ream.last_chunk_duration
            
            if "snapshot" in self.active_reams and "snapshot" in self.reams:
                ream = self.reams["snapshot"]
                snapshot_active = True
                snapshot_interval = ream.get_current_interval()
                snapshot_countdown = ream.minutes_until_next
            
            self.window_manager.draw_footer(footer_text)
            self.window_manager.draw_status(
                input_text=self.input_text,
                volume=volume,
                transcription_status=transcription_status,
                interview_active=interview_active,
                queue_size=queue_size,
                processing_time=processing_time,
                snapshot_active=snapshot_active,
                snapshot_interval=snapshot_interval,
                snapshot_countdown=snapshot_countdown
            )
            self.window_manager.refresh_all()
            log("draw_dashboard: complete")
        except Exception as e:
            log(f"draw_dashboard: exception: {type(e).__name__}: {str(e)[:80]}")
            import traceback
            log(f"Traceback: {traceback.format_exc()[:300]}")
            raise

    def run(self) -> None:
        """Main application loop."""
        import time
        from debug import log, clear_log
        
        clear_log()  # Start fresh
        log("run(): starting application")
        
        curses.curs_set(0)  # Hide cursor by default
        
        # Initialize session
        log("run(): calling init_session")
        if not self.init_session():
            log("run(): init_session failed")
            self.running = False
            return
        log("run(): init_session complete")
        
        self.stdscr.nodelay(True)  # Non-blocking input
        
        loop_count = 0
        while self.running:
            loop_count += 1
            if loop_count % 20 == 0:  # Log every 20 iterations (once per second)
                log(f"run(): loop iteration {loop_count}")
            
            try:
                # Add small delay to prevent rapid flashing
                time.sleep(0.05)
                
                self.draw_dashboard()
                
                ch = self.stdscr.getch()
                
                if ch == -1:
                    # No input available - continue to next frame
                    # Status bar updated in draw_dashboard()
                    continue
                
                log(f"run(): key pressed: {ch}")
                # Handle ream shortcuts
                if ch == 9:  # Ctrl+I - Toggle Interview
                    log("run(): Ctrl+I pressed")
                    self.toggle_ream("interview")
                    log("run(): Ctrl+I handled")
                    continue
                elif ch == 19:  # Ctrl+S - Toggle Snapshot
                    log("run(): Ctrl+S pressed")
                    self.toggle_ream("snapshot")
                    log("run(): Ctrl+S handled")
                    continue
                elif ch == 16:  # Ctrl+P - Manual snapshot trigger
                    if "snapshot" in self.reams and "snapshot" in self.active_reams:
                        self.reams["snapshot"].trigger_manual_snapshot()
                    continue
                elif ch == 17:  # Ctrl+Q - Quit
                    self.running = False
                    continue
                elif ch == curses.KEY_UP:  # Up arrow - Increase snapshot interval
                    if "snapshot" in self.reams and "snapshot" in self.active_reams:
                        self.reams["snapshot"].set_interval("up")
                    continue
                elif ch == curses.KEY_DOWN:  # Down arrow - Decrease snapshot interval
                    if "snapshot" in self.reams and "snapshot" in self.active_reams:
                        self.reams["snapshot"].set_interval("down")
                    continue
                
                # Observation is always active - handle text input
                if ch == curses.KEY_ENTER or ch == ord('\n'):  # Enter - Save
                    self.save_active_entry()
                elif ch == curses.KEY_BACKSPACE or ch == 127:  # Backspace
                    if self.input_text:
                        self.input_text = self.input_text[:-1]
                elif 32 <= ch <= 126:  # Printable characters
                    self.input_text += chr(ch)
                
            except Exception as e:
                log(f"run(): exception in main loop: {type(e).__name__}: {str(e)[:100]}")
                self.status_message = f"Error: {str(e)[:40]}"
                self.window_manager.draw_status(input_text=self.input_text)
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

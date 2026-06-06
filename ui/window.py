"""Curses-based window management for Fieldream UI."""

import curses
from math import inf
from typing import Optional, List, Dict


class WindowManager:
    """Manages curses windows and basic UI rendering."""

    def __init__(self, stdscr):
        """Initialize window manager.
        
        Args:
            stdscr: The curses standard screen object
        """
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        
        # Initialize color pairs
        self._init_colors()

    def _init_colors(self) -> None:
        """Initialize color pairs for the UI."""
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Header
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)   # Footer
            curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # Highlight
            curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Active ream
            curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)     # Inactive ream

    def draw_header(self, title: str, subtitle: str = "") -> None:
        """Draw the header bar."""
        try:
            self.stdscr.move(0, 0)
            self.stdscr.clrtoeol()
            if subtitle:
                header_text = f" {title} | {subtitle}"
            else:
                header_text = f" {title}"
            header_text = header_text[:self.width-1]
            self.stdscr.addstr(0, 0, header_text, curses.color_pair(1))
        except:
            pass

    def draw_footer(self, text: str) -> None:
        """Draw the footer bar with help text."""
        try:
            footer_y = self.height - 2
            self.stdscr.move(footer_y, 0)
            self.stdscr.clrtoeol()
            footer_text = f" {text}"
            footer_text = footer_text[:self.width-1]
            self.stdscr.addstr(footer_y, 0, footer_text, curses.color_pair(2))
        except:
            pass

    def draw_status(self, input_text: str = "", volume: float = 0, transcription_status: str = "", interview_active: bool = False) -> None:
        """Draw consolidated status bar at bottom.
        
        Args:
            input_text: Current input text for word/char count
            volume: Current audio volume (0-1)
            transcription_status: Status message from Interview ([silence], [voice], [processing], [done])
            interview_active: Whether Interview ream is active
        """
        try:
            status_y = self.height - 1
            self.stdscr.move(status_y, 0)
            self.stdscr.clrtoeol()
            
            # Calculate word and character count
            text_to_count = input_text.strip()
            char_count = len(text_to_count)
            word_count = len(text_to_count.split()) if text_to_count else 0
            
            # Build status text
            status_parts = [f" Words: {word_count} | Chars: {char_count}"]
            
            # Add audio meter and status if Interview is active
            if interview_active:
                # Convert volume (0-1) to meter visualization
                meter_width = 8
                filled = int(volume * meter_width)
                meter = "█" * filled + "░" * (meter_width - filled)
                
                # Convert RMS to dB (rough approximation: 20*log10(rms))
                db = 20 * (volume ** 0.5) - 30 if volume > 0 else -inf
                
                status_parts.append(f" | [{meter}] {db:+.0f}dB | {transcription_status}")
            
            status_text = "".join(status_parts)
            status_text = status_text[:self.width-1]
            self.stdscr.addstr(status_y, 0, status_text)
        except:
            pass

    def refresh_all(self) -> None:
        """Refresh screen."""
        try:
            self.stdscr.refresh()
        except:
            pass

    def draw_dashboard(self, session_name: str, reams: List[Dict], ream_contents: Dict[str, str] = None, 
                       input_text: str = "", scroll_offsets: Dict[str, int] = None) -> None:
        """Draw the dashboard."""
        if ream_contents is None:
            ream_contents = {}
        if scroll_offsets is None:
            scroll_offsets = {}
        
        try:
            # Clear content area
            for y in range(1, self.height - 2):
                self.stdscr.move(y, 0)
                self.stdscr.clrtoeol()
            
            # Draw session header
            session_text = f"Session: {session_name}"[:self.width-1]
            self.stdscr.addstr(1, 0, session_text, curses.A_BOLD)
            
            # Draw separator
            self.stdscr.addstr(2, 0, "=" * (self.width - 1))
            
            # Draw 3 columns
            col_width = (self.width - 4) // 3
            row = 3
            
            for col_idx, ream in enumerate(reams):
                if col_idx >= 3:
                    break
                if row >= self.height - 2:
                    break
                
                col_x = col_idx * (col_width + 2)
                key = ream.get("key")
                is_active = ream.get("active", False)
                
                # Column header
                status_char = "*" if is_active else " "
                header = f"[{status_char}] {ream['name']}"[:col_width]
                color = curses.color_pair(4) if is_active else curses.color_pair(5)
                self.stdscr.addstr(row, col_x, header, color | curses.A_BOLD)
                
                # Calculate input display lines first (only for Observation)
                input_display_lines = []
                if key == "observation":
                    if input_text:
                        input_str = "> " + input_text
                    else:
                        input_str = "> "
                    
                    while len(input_str) > col_width:
                        input_display_lines.append(input_str[:col_width])
                        input_str = input_str[col_width:]
                    if input_str:
                        input_display_lines.append(input_str)
                
                # Calculate content boundary (input grows upward from height-3)
                num_input_lines = len(input_display_lines)
                max_content_row = self.height - 3 - num_input_lines
                display_height = max_content_row - row - 1
                
                # Wrap and display content lines
                lines = ream_contents.get(key, "").split("\n") if key in ream_contents else []
                
                # Convert lines to wrapped lines
                wrapped_lines = []
                for line in lines:
                    while len(line) > col_width:
                        wrapped_lines.append(line[:col_width])
                        line = line[col_width:]
                    wrapped_lines.append(line)
                
                # Auto-scroll to bottom if content grew
                total_wrapped = len(wrapped_lines)
                if total_wrapped > display_height:
                    # Show the last display_height lines
                    offset = total_wrapped - display_height
                else:
                    offset = 0
                
                scroll_offsets[key] = offset
                
                # Display wrapped content lines (from row+1 onwards, up to max_content_row)
                display_row = 0
                for i in range(offset, len(wrapped_lines)):
                    current_row = row + 1 + display_row
                    if current_row >= max_content_row:
                        break
                    
                    display_line = wrapped_lines[i]
                    self.stdscr.addstr(current_row, col_x, display_line[:col_width])
                    display_row += 1
                
                # Display input lines if Observation (grows upward from height-3)
                if key == "observation" and input_display_lines:
                    input_start_row = self.height - 3 - num_input_lines
                    for idx, input_line in enumerate(input_display_lines):
                        current_row = input_start_row + idx
                        if current_row >= self.height - 2:
                            break
                        
                        self.stdscr.addstr(current_row, col_x, input_line[:col_width], curses.color_pair(3))
            
            self.stdscr.refresh()
        except Exception as e:
            pass

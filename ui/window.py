"""Curses-based window management for Fieldream UI."""

import curses
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

    def draw_status(self, message: str) -> None:
        """Draw status message at bottom."""
        try:
            status_y = self.height - 1
            self.stdscr.move(status_y, 0)
            self.stdscr.clrtoeol()
            status_text = f" {message}"
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
                       input_text: str = "", active_ream: str = None, scroll_offsets: Dict[str, int] = None) -> None:
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
                
                # Content lines
                lines = ream_contents.get(key, "").split("\n") if key in ream_contents else []
                offset = scroll_offsets.get(key, 0)
                
                for i in range(1, col_width // 2):
                    if row + i >= self.height - 3:
                        break
                    
                    line_idx = offset + i - 1
                    if line_idx < len(lines):
                        line = lines[line_idx][:col_width]
                    else:
                        line = ""
                    
                    self.stdscr.addstr(row + i, col_x, line)
                
                # Input line if active
                if is_active:
                    input_row = row + col_width // 2
                    if input_row < self.height - 3:
                        input_str = ("> " + input_text)[:col_width]
                        self.stdscr.addstr(input_row, col_x, input_str, curses.color_pair(3))
            
            self.stdscr.refresh()
        except Exception as e:
            pass

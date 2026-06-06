"""Curses-based window management for Fieldream UI."""

import curses
from typing import Optional, Callable, List, Dict


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
        
        # Create sub-windows
        self.header_win = curses.newwin(1, self.width, 0, 0)
        self.content_win = curses.newwin(
            self.height - 3, self.width, 1, 0
        )
        self.footer_win = curses.newwin(1, self.width, self.height - 2, 0)
        self.status_win = curses.newwin(1, self.width, self.height - 1, 0)
        
        self.content_win.scrollok(True)

    def _init_colors(self) -> None:
        """Initialize color pairs for the UI."""
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Header
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)   # Footer
            curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # Highlight
            curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Active ream
            curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)     # Inactive ream

    def draw_header(self, title: str, subtitle: str = "") -> None:
        """Draw the header bar.
        
        Args:
            title: Application title
            subtitle: Optional subtitle
        """
        self.header_win.clear()
        if subtitle:
            header_text = f" {title} | {subtitle}"
        else:
            header_text = f" {title}"
        self.header_win.addstr(0, 0, header_text[:self.width], curses.color_pair(1))
        self.header_win.refresh()

    def draw_footer(self, text: str) -> None:
        """Draw the footer bar with help text.
        
        Args:
            text: Footer text
        """
        self.footer_win.clear()
        footer_text = f" {text}"
        self.footer_win.addstr(0, 0, footer_text[:self.width], curses.color_pair(2))
        self.footer_win.refresh()

    def draw_status(self, message: str) -> None:
        """Draw status message at bottom.
        
        Args:
            message: Status message to display
        """
        try:
            self.status_win.clear()
            status_text = f" {message}"[:self.width - 1]
            self.status_win.addstr(0, 0, status_text)
            self.status_win.refresh()
        except:
            pass

    def get_content_area(self):
        """Return the content window for writing."""
        return self.content_win

    def clear_content(self) -> None:
        """Clear the content area."""
        self.content_win.clear()

    def refresh_all(self) -> None:
        """Refresh all windows."""
        self.header_win.refresh()
        self.content_win.refresh()
        self.footer_win.refresh()
        self.status_win.refresh()

    def getch(self) -> int:
        """Get a single character input (non-blocking if set).
        
        Returns:
            Character code
        """
        return self.stdscr.getch()

    def draw_dashboard(self, session_name: str, reams: List[Dict], ream_contents: Dict[str, str] = None, 
                       input_text: str = "", active_ream: str = None, scroll_offsets: Dict[str, int] = None) -> None:
        """Draw the 3-column ream dashboard.
        
        Args:
            session_name: Current session name
            reams: List of ream dictionaries with status
            ream_contents: Dict mapping ream key to file contents
            input_text: Current input text if a ream is active
            active_ream: Key of the currently active ream
            scroll_offsets: Dict mapping ream key to scroll offset
        """
        if ream_contents is None:
            ream_contents = {}
        if scroll_offsets is None:
            scroll_offsets = {}
        
        self.clear_content()
        content_win = self.get_content_area()
        content_win.clear()
        
        # Column dimensions
        col_width = max(20, self.width // 3 - 1)  # Ensure minimum width
        col_height = max(5, self.height - 4)
        
        # Draw session info at top
        session_text = f"Session: {session_name}"
        safe_session = session_text[:self.width-2]
        if len(safe_session) <= self.width:
            content_win.addstr(0, 0, safe_session, curses.A_BOLD)
        
        divider = "─" * (self.width - 1)
        content_win.addstr(1, 0, divider[:self.width])
        
        row_start = 2
        
        # Draw 3 columns
        for col_idx, ream in enumerate(reams):
            if col_idx >= 3:
                break
            
            col_x = col_idx * (col_width + 1)
            
            # Skip if column would be completely off-screen
            if col_x >= self.width:
                break
            
            key = ream.get("key")
            is_active = ream.get("active", False)
            status_color = curses.color_pair(4) if is_active else curses.color_pair(5)
            status_text = "●" if is_active else "○"
            
            # Draw column header
            ream_name = ream['name'][:col_width-4]
            header = f"{ream_name} {status_text}"
            header_safe = header[:col_width]
            
            if col_x < self.width:
                content_win.addstr(row_start, col_x, header_safe.ljust(min(col_width, self.width - col_x)), status_color | curses.A_BOLD)
            
            # Draw column divider
            if col_idx < 2:  # Don't draw right border for last column
                divider_x = col_x + col_width
                if divider_x < self.width:
                    for dy in range(col_height + 1):
                        if row_start + dy < self.height:
                            try:
                                content_win.addch(row_start + dy, divider_x, ord("│"))
                            except:
                                pass
            
            # Draw file contents
            content_lines = ream_contents.get(key, "").split("\n") if key in ream_contents else []
            scroll_offset = scroll_offsets.get(key, 0)
            
            display_height = col_height - 2 if is_active else col_height - 1
            
            for dy in range(display_height):
                line_idx = scroll_offset + dy
                if line_idx < len(content_lines):
                    line = content_lines[line_idx][:col_width]
                else:
                    line = ""
                
                content_y = row_start + 1 + dy
                if col_x < self.width and content_y < self.height:
                    safe_width = min(col_width, self.width - col_x)
                    try:
                        content_win.addstr(content_y, col_x, line.ljust(safe_width)[:safe_width])
                    except:
                        pass
            
            # Draw input area if active
            if is_active:
                input_y = row_start + col_height - 1
                if input_y < self.height:
                    input_prompt = "> "
                    input_display = (input_prompt + input_text)[:col_width]
                    safe_width = min(col_width, self.width - col_x)
                    try:
                        content_win.addstr(input_y, col_x, input_display.ljust(safe_width)[:safe_width], curses.color_pair(3))
                    except:
                        pass
        
        content_win.refresh()

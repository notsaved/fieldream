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
        
        try:
            self.clear_content()
            content_win = self.get_content_area()
            content_win.clear()
            
            max_y, max_x = self.height - 4, self.width
            
            # Draw session info at top
            session_text = f"Session: {session_name}"[:max_x-1]
            content_win.addstr(0, 0, session_text, curses.A_BOLD)
            content_win.addstr(1, 0, "=" * (max_x - 1))
            
            # Simple text-only layout for now
            row = 2
            col_width = (max_x - 4) // 3
            
            for col_idx, ream in enumerate(reams):
                if col_idx >= 3 or row >= max_y:
                    break
                
                col_x = col_idx * (col_width + 2)
                if col_x >= max_x:
                    break
                
                key = ream.get("key")
                is_active = ream.get("active", False)
                status = "[●]" if is_active else "[ ]"
                
                # Header
                header = f"{ream['name'][:col_width-5]} {status}"
                header_safe = header[:col_width]
                try:
                    content_win.addstr(row, col_x, header_safe, curses.color_pair(4 if is_active else 5) | curses.A_BOLD)
                except:
                    pass
                
                # Content
                lines = ream_contents.get(key, "").split("\n") if key in ream_contents else []
                offset = scroll_offsets.get(key, 0)
                
                for i in range(1, col_width // 2):
                    line_idx = offset + i - 1
                    if row + i >= max_y:
                        break
                    
                    if line_idx < len(lines):
                        line = lines[line_idx][:col_width]
                    else:
                        line = ""
                    
                    try:
                        content_win.addstr(row + i, col_x, line.ljust(col_width)[:col_width])
                    except:
                        pass
                
                # Input line if active
                if is_active:
                    input_row = row + col_width // 2
                    if input_row < max_y:
                        input_str = ("> " + input_text)[:col_width]
                        try:
                            content_win.addstr(input_row, col_x, input_str.ljust(col_width)[:col_width], curses.color_pair(3))
                        except:
                            pass
            
            content_win.refresh()
        except Exception as e:
            pass

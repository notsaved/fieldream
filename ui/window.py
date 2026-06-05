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
        self.status_win.clear()
        self.status_win.addstr(0, 0, f" {message}"[:self.width])
        self.status_win.refresh()

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

    def draw_dashboard(self, session_name: str, reams: List[Dict]) -> None:
        """Draw the ream dashboard showing status of each ream.
        
        Args:
            session_name: Current session name
            reams: List of ream dictionaries with status
        """
        self.clear_content()
        content_win = self.get_content_area()
        content_win.clear()
        
        row = 1
        content_win.addstr(row, 2, f"Session: {session_name}", curses.color_pair(3))
        row += 3
        
        content_win.addstr(row, 2, "Available Reams:", curses.A_BOLD)
        row += 2
        
        for ream in reams:
            active = ream.get("active", False)
            status = "● ACTIVE" if active else "○ inactive"
            color_pair = curses.color_pair(4) if active else curses.color_pair(5)
            
            line = f"  [{ream['shortcut']}] {ream['name']:<15} {status}"
            content_win.addstr(row, 2, line, color_pair)
            content_win.addstr(row + 1, 4, ream['description'])
            row += 3
        
        content_win.refresh()

"""Debug logging utility for Fieldream."""

from datetime import datetime
from pathlib import Path

DEBUG_FILE = Path.home() / "fieldream_debug.log"

def log(message: str) -> None:
    """Write debug message to log file."""
    try:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        with open(DEBUG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

def clear_log() -> None:
    """Clear debug log."""
    try:
        DEBUG_FILE.write_text("")
    except:
        pass

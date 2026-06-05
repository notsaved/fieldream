"""Configuration settings for Fieldream."""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent

# Notes directory on Desktop (or user home if Desktop doesn't exist)
DESKTOP_DIR = Path.home() / "Desktop"
if DESKTOP_DIR.exists():
    NOTES_DIR = DESKTOP_DIR / "Fieldream"
else:
    NOTES_DIR = Path.home() / "Fieldream"

# Ensure notes directory exists
NOTES_DIR.mkdir(exist_ok=True)

# Ream configurations (order matters for display)
REAMS = [
    {
        "key": "observation",
        "name": "Observation",
        "shortcut": "Ctrl+O",
        "description": "Text-based note taking",
        "file_prefix": "observation",
    },
    {
        "key": "interview",
        "name": "Interview",
        "shortcut": "Ctrl+I",
        "description": "Speech-to-text transcription",
        "file_prefix": "interview",
    },
    {
        "key": "snapshot",
        "name": "Snapshot",
        "shortcut": "Ctrl+S",
        "description": "Image-to-text from camera",
        "file_prefix": "snapshot",
    },
]

# UI settings
UI_COLORS = {
    "default": 0,
    "header": 1,
    "footer": 2,
    "highlight": 3,
}

# Status messages
STATUS_MESSAGES = {
    "ream_changed": "Ream changed to: {}",
    "note_saved": "Note saved to: {}",
    "error": "Error: {}",
    "info": "{}",
}

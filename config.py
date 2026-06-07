"""Configuration settings for Fieldream."""

from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent

# Note: NOTES_DIR is set dynamically at runtime after user selects location
# We don't create any folders at startup - user will choose location first

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

# Ethnographic image description prompt for Snapshot ream
ETHNOGRAPHIC_IMAGE_PROMPT = """Analyze this image from an ethnographic perspective. Describe:
1. Main subjects/people (if present) - activities, positioning, expressions
2. Cultural context - what cultural practice or setting is this?
3. Material culture - objects, tools, clothing, artifacts visible
4. Social relations - group dynamics, relationships implied
5. Spatial context - where is this? What does the space tell us?
Provide a concise, observational ethnographic description."""

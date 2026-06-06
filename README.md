# Fieldream - Offline Note-Taking System for Raspberry Pi 5

A terminal-based note-taking system designed for Raspberry Pi 5 with AI hat, featuring multiple "reams" (modes) for different types of note-taking.

## Features

- **Offline-first**: Works completely offline
- **3-Column Dashboard**: View all active reams side-by-side with live content
- **Keyboard-driven UI**: Terminal interface with Curses
- **Multiple Reams**: Extensible ream system
  - **Observation**: Type and append text notes
  - **Interview**: Speech-to-text transcription (planned)
  - **Snapshot**: Image-to-text from camera (planned)
- **Scrollable Views**: Read past entries while continuing to type
- **Session Management**: Organize notes by session with custom naming and save locations

## Installation

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

## Quick Start

1. Run `python main.py`
2. Enter a session name (e.g., "Field Research Day 1")
3. Choose where to save: **R**oot, **D**esktop, **D**ocuments, or **T**arget folder
4. Use **Ctrl+O** to activate Observation mode
5. Type notes and press **Enter** to save
6. Use **↑/↓** arrows to scroll through your notes
7. Press **Ctrl+Q** to quit

## Keyboard Controls

**Dashboard Mode:**
- **Ctrl+O** - Toggle Observation mode
- **Ctrl+I** - Toggle Interview mode (planned)
- **Ctrl+S** - Toggle Snapshot mode (planned)
- **↑/↓** - Scroll active ream
- **Ctrl+Q** - Quit

**Active Ream Mode:**
- **Type** - Enter text
- **Enter** - Save entry and clear input
- **Backspace** - Delete character
- **↑/↓** - Scroll through past entries
- **Ctrl+Q** - Deactivate ream

## Project Structure

```
fieldream/
├── main.py              # Application entry point
├── config.py            # Configuration & ream definitions
├── requirements.txt     # Python dependencies
├── ui/                  # Curses-based UI
│   ├── window.py        # Window management & rendering
│   └── startup.py       # Session creation & setup
├── reams/               # Note-taking mode implementations
│   ├── base.py          # Base ream class
│   └── observation.py   # Observation ream
└── utils/
    └── file_handler.py  # Markdown file I/O
```

## File Format

Notes are saved as markdown files with timestamps:

```markdown
# Observation
**Date:** 2026-06-06  
**Started:** 14:30:22

**[14:30:35]**
First observation text...

**[14:32:10]**
Second observation text...
```

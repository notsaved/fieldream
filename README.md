# Fieldream - Offline Note-Taking System for Raspberry Pi 5

A terminal-based note-taking system designed for Raspberry Pi 5 with AI hat, featuring multiple "reams" (modes) for different types of note-taking.

## Features

- **Offline-first**: Works completely offline
- **Curses UI**: Keyboard-driven terminal interface
- **Multiple Reams**: Extensible ream system for different note-taking modes
  - **Observation**: Type and append text notes
  - **Interview**: Speech-to-text transcription
  - **Snapshot**: Image-to-text from camera captures

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

## Project Structure

- `main.py`: Application entry point
- `config.py`: Configuration settings
- `ui/`: Curses-based UI components
- `reams/`: Ream implementations
- `utils/`: Utility functions for file operations
- `notes/`: Directory containing markdown note files

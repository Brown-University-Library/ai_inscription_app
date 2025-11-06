# Leiden to EpiDoc Converter

A desktop application for converting epigraphic and papyrological inscriptions from Leiden Convention format to EpiDoc XML using Claude AI.

## Overview

This application provides a user-friendly GUI for converting inscriptions written in Leiden Convention to properly formatted EpiDoc XML. It leverages Anthropic's Claude AI to perform accurate, context-aware conversions while preserving all meaningful information.

## Features

- **AI-Powered Conversion**: Uses Claude AI for intelligent Leiden to EpiDoc translation
- **Native GUI**: Clean, responsive interface built with PySide6/Qt
- **Unicode Support**: Full support for Greek, Hebrew, Arabic, and other ancient scripts
- **RTL Languages**: Automatic right-to-left text rendering for Hebrew, Arabic, and Syriac
- **Non-Blocking Operations**: Conversions run in background threads to keep UI responsive
- **File Management**: Load Leiden text from files and save EpiDoc XML output
- **Configurable**: Customize API settings and default save locations
- **Cross-Platform**: Runs on Linux, Windows, and macOS with native appearance

## Installation

### Prerequisites

- Python 3.12 or higher
- An Anthropic API key ([get one here](https://console.anthropic.com/))

### Install Dependencies

Using `uv` (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -e .
```

## Usage

### Running the Application

Using `uv`:
```bash
uv run python leiden-epidoc.py
```

Or directly with Python:
```bash
python leiden-epidoc.py
```

### First Time Setup

1. Launch the application
2. Go to **Settings → Configure API**
3. Enter your Anthropic API key
4. (Optional) Select a different Claude model if desired
5. Click **Save**

### Converting Text

1. **Input Leiden text**:
   - Type directly into the input box, or
   - Click **Load from File** to load a `.txt` file

2. **Convert**:
   - Click the **Convert to EpiDoc** button
   - Wait for the conversion to complete (status shown in status bar)

3. **Save output**:
   - Review the EpiDoc XML in the output box
   - Click **Save Output to File** to save as `.xml`

### Settings

- **Configure API**: Set or change your Anthropic API key and model
- **Set Save Location**: Choose default directory for saving output files

## Configuration

Settings are stored in `leiden_epidoc_config.json` in the application directory:

```json
{
  "api_key": "your-api-key-here",
  "model": "claude-sonnet-4-20250514",
  "save_location": "/path/to/save/directory"
}
```

## Architecture

### Main Components

- **LeidenToEpiDocConverter**: Core conversion logic, API client management
- **ConversionThread**: Background thread for non-blocking API calls
- **LeidenEpiDocGUI**: Main application window (QMainWindow)
- **APISettingsDialog**: Dialog for API configuration
- **SaveLocationDialog**: Dialog for setting default save location

### Technology Stack

- **PySide6**: Qt bindings for Python (GUI framework)
- **Anthropic API**: Claude AI for conversion logic
- **Python 3.12+**: Modern Python with type hints

## Platform Support

The application uses Qt's native widgets and automatically adapts to your operating system:

- **Linux**: GTK/KDE integration with system theme
- **Windows**: Native Windows controls and styling
- **macOS**: Native macOS appearance and behavior

## Supported Scripts

Qt automatically handles Unicode text rendering for:
- Latin (basic and extended)
- Greek (including polytonic)
- Hebrew
- Arabic
- Coptic
- Cyrillic
- Syriac
- Armenian
- And many more...

## Future Enhancements

Potential improvements:
- Syntax highlighting for XML output
- Drag-and-drop file loading
- Recent files menu
- Split view for side-by-side comparison
- Dark mode / custom themes
- Keyboard shortcuts
- Undo/redo support
- Batch conversion

## License

See LICENSE file for details.

## Contributing

Contributions welcome! Please submit issues and pull requests on GitHub.

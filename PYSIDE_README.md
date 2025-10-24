# PySide6 Implementation

## Overview

`leiden-epidoc-pyside.py` is a PySide6-based GUI implementation of the Leiden to EpiDoc converter, providing a native Qt interface as an alternative to the DearPyGui version.

## Key Features

### Same Core Functionality
- Converts Leiden Convention inscriptions to EpiDoc XML using Claude API
- RTL (Right-to-Left) language support with visual preview
- Configurable language/script support
- API key and model configuration
- Custom save location settings

### PySide6 Advantages

1. **Native Look and Feel**: Uses Qt widgets for a more native appearance on all platforms
2. **Better Font Support**: Built-in Unicode font rendering without manual glyph loading
3. **Threaded Operations**: Conversion runs in a separate thread to prevent UI freezing
4. **Standard Dialogs**: Uses native file dialogs and message boxes
5. **Better Layout Management**: Qt's layout system is more robust and flexible
6. **Accessibility**: Better support for screen readers and accessibility features

## Installation

The PySide6 dependency is already added to `pyproject.toml`. Install with:

```bash
uv sync
# or
pip install -e .
```

## Running the Application

```bash
uv run python leiden-epidoc-pyside.py
# or
python leiden-epidoc-pyside.py
```

## Differences from DearPyGui Version

### User Interface
- **Menu System**: Standard menu bar with File and Settings menus
- **Dialogs**: Modal dialogs for settings (API, Language, Save Location)
- **Layout**: Vertical layout with clearly separated sections
- **Threading**: Conversion happens in background thread with status updates

### Technical Differences
- **Threading**: Uses `QThread` for async operations instead of blocking UI
- **Widgets**: QTextEdit for text input/output instead of DearPyGui input_text
- **Dialogs**: Custom QDialog classes for settings instead of DearPyGui windows
- **File Selection**: Native Qt file dialogs instead of DearPyGui file_dialog

### Configuration
- Both versions share the same `leiden_epidoc_config.json` configuration file
- Settings are interchangeable between versions

## Architecture

### Main Classes

1. **LeidenToEpiDocConverter**: Core conversion logic (unchanged from DPG version)
2. **ConversionThread**: QThread subclass for non-blocking API calls
3. **LeidenEpiDocGUI**: Main window (QMainWindow)
4. **APISettingsDialog**: QDialog for API configuration
5. **LanguageSettingsDialog**: QDialog for language/script settings
6. **SaveLocationDialog**: QDialog for save location configuration

### Signal/Slot System

PySide6 uses Qt's signal/slot mechanism for event handling:
- Button clicks trigger slot methods
- Thread completion emits signals to update UI
- Text changes trigger callbacks for logical text storage

## RTL Support

RTL preview works the same way as in the DPG version:
- Checkbox to enable RTL visual preview
- Uses `python-bidi` library for BiDi algorithm
- Input becomes read-only in preview mode
- Logical text is preserved for conversion

## Platform Support

PySide6 provides excellent cross-platform support:
- **Linux**: Native Qt widgets with system theme
- **Windows**: Native Windows controls
- **macOS**: Native macOS appearance

## Memory and Performance

Font handling is simpler in PySide6:
- No manual glyph range loading required
- Qt handles Unicode font rendering automatically
- Lower memory footprint for font support
- Faster startup time

## Future Enhancements

Potential improvements unique to PySide6:
- Syntax highlighting for XML output (using QSyntaxHighlighter)
- Drag-and-drop file loading
- Recent files menu
- Split view for side-by-side comparison
- Custom themes/stylesheets
- Keyboard shortcuts
- Undo/redo support

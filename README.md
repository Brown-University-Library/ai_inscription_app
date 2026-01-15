# Leiden to EpiDoc Converter

A desktop application for converting epigraphic and papyrological inscriptions from Leiden Convention format to EpiDoc XML using Claude AI.

## Overview

This application provides a user-friendly GUI for converting inscriptions written in Leiden Convention to properly formatted EpiDoc XML. It leverages Anthropic's Claude AI to perform accurate, context-aware conversions while preserving all meaningful information.

## Features

- **AI-Powered Conversion**: Uses Claude AI for intelligent Leiden to EpiDoc translation
- **Native GUI**: Clean, responsive interface built with PySide6/Qt
- **Unicode Support**: Full support for Greek, Hebrew, Arabic, and other ancient scripts
- **RTL Languages**: Automatic right-to-left text rendering for Hebrew, Arabic, and Syriac
- **File Management**: Load Leiden text from files and save EpiDoc XML output
- **Configurable**: Customize API settings and default save locations
- **Cross-Platform**: Runs on Linux, Windows, and macOS with native appearance

## Quick Start (Pre-built Downloads)

Pre-built executables are available for Windows and macOS. No Python installation required!

### Download

Download the latest release for your platform from the [Releases page](https://github.com/Brown-University-Library/ai_inscription_app/releases/latest):

| Platform | File | Instructions |
|----------|------|--------------|
| **Windows** | `LeidenToEpiDoc.exe` | Download and run directly |
| **macOS** | `LeidenToEpiDoc-Mac.zip` | Download, unzip, and open the `.app` |

### Windows

1. Download `LeidenToEpiDoc.exe` from the [latest release](https://github.com/Brown-University-Library/ai_inscription_app/releases/latest)
2. Double-click the downloaded file to run the application
3. If Windows SmartScreen appears, click **More info** → **Run anyway** (the app is not code-signed)
4. On first launch, go to **Settings → Configure API** and enter your [Anthropic API key](https://console.anthropic.com/)

### macOS

1. Download `LeidenToEpiDoc-Mac.zip` from the [latest release](https://github.com/Brown-University-Library/ai_inscription_app/releases/latest)
2. Double-click the ZIP file to extract it (creates `leiden-epidoc.app`)
3. Right-click the app and select **Open** (required for first launch since the app is not notarized)
4. If prompted, click **Open** again in the security dialog
5. On first launch, go to **Settings → Configure API** and enter your [Anthropic API key](https://console.anthropic.com/)

> **Note**: You will need an Anthropic API key to use this application. Get one at [console.anthropic.com](https://console.anthropic.com/).

---

## Installation from Source

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

## Testing

This project includes a comprehensive test suite to ensure code quality and reliability.

### Running Tests

Install test dependencies:
```bash
pip install -e ".[test]"
```

Run all tests:
```bash
pytest
```

Run tests with coverage report:
```bash
pytest --cov=. --cov-report=html
```

Run specific test files:
```bash
pytest tests/test_converter.py
pytest tests/test_prompts.py
pytest tests/test_integration.py
```

Run tests by marker:
```bash
pytest -m unit           # Run only unit tests
pytest -m integration    # Run only integration tests
```

### Test Structure

The test suite is organized into several categories:

- **`tests/test_converter.py`**: Unit tests for the `LeidenToEpiDocConverter` class
  - Configuration loading and saving
  - Response parsing logic
  - Error handling
  - Custom prompt/examples functionality
  - Regex pattern validation

- **`tests/test_file_item.py`**: Unit tests for the `FileItem` class
  - File loading and content management
  - Unicode support
  - File property handling

- **`tests/test_prompts.py`**: Tests for the prompt system
  - System instruction validation
  - Examples structure verification
  - Leiden Convention coverage
  - EpiDoc tag coverage

- **`tests/test_integration.py`**: Integration tests for complete workflows
  - End-to-end conversion workflows
  - Configuration management
  - Custom prompts and examples
  - File handling and batch operations

### Test Coverage

The test suite covers:
- ✅ Configuration loading and saving
- ✅ File loading and content management
- ✅ Response parsing with various tag combinations
- ✅ Error handling (missing API key, file errors, API errors)
- ✅ Custom prompts and examples
- ✅ Unicode and multilingual text support
- ✅ Batch file processing
- ✅ Output file naming and collision handling
- ✅ Leiden Convention and EpiDoc instruction validation

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

## License

See LICENSE file for details.

## Contributing

Contributions welcome! Please submit issues and pull requests on GitHub.

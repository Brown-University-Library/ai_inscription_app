# GitHub Copilot Instructions for AI Inscription App

## Project Overview

This is a desktop application for converting epigraphic and papyrological inscriptions from Leiden Convention format to EpiDoc XML using Claude AI. The application provides a user-friendly GUI built with PySide6/Qt that leverages Anthropic's Claude AI for intelligent, context-aware conversions.

## Technology Stack

- **Python**: 3.12+ (modern Python with type hints)
- **GUI Framework**: PySide6 (Qt6 bindings for Python)
- **AI Service**: Anthropic Claude API
- **Package Manager**: `uv` (modern Python package manager)
- **Dependencies**: Listed in `pyproject.toml`

## Code Structure

### Main Components

- **`leiden-epidoc.py`**: Main application file containing:
  - `LeidenToEpiDocConverter`: Core conversion logic and API client management
  - `ConversionThread`: Background thread for non-blocking API calls
  - `LeidenEpiDocGUI`: Main application window (QMainWindow)
  - `APISettingsDialog`: Dialog for API configuration
  - `SaveLocationDialog`: Dialog for setting default save location

- **`leiden_prompts.py`**: Contains system instructions and examples for Claude AI:
  - `SYSTEM_INSTRUCTION`: Detailed prompt for the AI conversion
  - `EXAMPLES_TEXT`: Example conversions for few-shot learning

- **`pyproject.toml`**: Python project configuration and dependencies
- **`leiden_epidoc_config.json`**: Runtime configuration (API key, model, save location)

## Development Guidelines

### Setting Up Development Environment

```bash
# Install dependencies using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### Running the Application

```bash
# Using uv
uv run python leiden-epidoc.py

# Or directly
python leiden-epidoc.py
```

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints for function parameters and return values
- Maintain clear docstrings for classes and complex methods
- Keep UI-related code separate from business logic

### Key Considerations

1. **Threading**: All API calls run in `ConversionThread` to keep UI responsive
2. **Unicode Support**: Full support for ancient scripts (Greek, Hebrew, Arabic, Coptic, etc.)
3. **RTL Text**: Right-to-left rendering for Hebrew, Arabic, and Syriac
4. **Configuration**: Settings stored in JSON file for persistence
5. **Error Handling**: Graceful error handling with user-friendly messages

### API Integration

- The application uses Anthropic's Claude API (default model: claude-sonnet-4-20250514)
- API key is stored securely in `leiden_epidoc_config.json` (not in version control)
- Conversion logic uses sophisticated prompting with examples for accuracy

### GUI Architecture

- Built on Qt's Model-View pattern
- Responsive layout using QSplitter for resizable panels
- Non-blocking operations via QThread
- Native platform integration (adapts to Linux/Windows/macOS)

## Best Practices for Changes

1. **Maintain Separation**: Keep conversion logic separate from GUI code
2. **Test with Real Data**: Use actual Leiden Convention text for testing
3. **Handle Errors Gracefully**: All API failures should show user-friendly messages
4. **Preserve Unicode**: Ensure all text operations preserve Unicode characters
5. **Keep UI Responsive**: Never block the main thread with long operations
6. **Configuration Safety**: Never commit API keys or sensitive data

## Common Tasks

### Adding a New Feature

1. Determine if it's GUI or logic-related
2. For GUI: Add to `LeidenEpiDocGUI` class
3. For logic: Add to `LeidenToEpiDocConverter` class
4. If it involves AI: Update prompts in `leiden_prompts.py`
5. Test with the full workflow (load → convert → save)

### Modifying Conversion Logic

1. Update the relevant prompt in `leiden_prompts.py`
2. Test with diverse Leiden Convention examples
3. Verify EpiDoc XML output validity
4. Ensure backward compatibility with existing configurations

### Updating Dependencies

```bash
# Using uv
uv add <package-name>

# Or manually edit pyproject.toml and run
uv sync
```

## Testing Approach

Currently, this project relies on manual testing:
- Load sample Leiden text
- Verify conversion accuracy
- Check XML output validity
- Test UI responsiveness
- Verify file operations (load/save)

## Known Limitations

- No automated test suite (manual testing only)
- API key required for functionality
- Internet connection needed for conversions
- No syntax highlighting in output (plain text display)

## Future Enhancement Ideas

- Syntax highlighting for XML output
- Drag-and-drop file loading
- Recent files menu
- Split view for side-by-side comparison
- Dark mode / custom themes
- Keyboard shortcuts
- Batch conversion support
- Offline validation mode

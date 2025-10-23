# Leiden → EpiDoc Converter (Dear PyGui)

A small GUI app to convert Leiden Convention text to EpiDoc XML using Anthropic models.

## Features
- Paste or load Leiden text
- Convert to EpiDoc XML
- Save output to file
- RTL preview support for input (Hebrew/Arabic/etc.)
- Horizontal Scroll Viewer for long lines (read-only)

## Horizontal scrolling
Dear PyGui's multiline input widget doesn’t show a visible horizontal scrollbar on some setups. To inspect long lines without soft-wrapping, use:

- Menu: View → Open Horizontal Scroll Viewer
- This opens a window with two panes (input/output) that have horizontal scrollbars enabled and no wrapping.

Tip: You can still select/copy from the main output box or save to a file. The viewer is intended for comfortable inspection of long lines.

## Running
From the project folder:

```bash
uv run python ai_inscription_app/leiden-epidoc-dpg.py
```

## Configuration
- Open Settings → Configure API to set your Anthropic API key and model.
- Language/Script Support controls font glyph ranges to display various scripts.
- Save Location controls the default directory used by the Save dialog.

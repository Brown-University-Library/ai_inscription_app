# Comparison: DearPyGui vs PySide6 Implementation

## Quick Reference

| Feature | DearPyGui (`leiden-epidoc-dpg.py`) | PySide6 (`leiden-epidoc-pyside.py`) |
|---------|-----------------------------------|-------------------------------------|
| **UI Framework** | DearPyGui (immediate mode GPU) | Qt/PySide6 (retained mode native) |
| **Look & Feel** | Custom rendered | Native OS widgets |
| **Threading** | Blocking UI during conversion | Non-blocking with QThread |
| **Font Handling** | Manual glyph range loading | Automatic Unicode support |
| **Memory Usage** | Higher (GPU buffers + fonts) | Lower (native rendering) |
| **Startup Time** | Slower (font loading) | Faster |
| **File Dialogs** | Custom DPG dialogs | Native OS dialogs |
| **Platform Integration** | Limited | Excellent (system themes, etc.) |
| **Accessibility** | Limited | Full Qt accessibility support |
| **Dependencies** | dearpygui, dearpygui-ext | PySide6 |

## When to Use Each

### Use DearPyGui Version When:
- You need immediate mode rendering
- You want custom GPU-accelerated UI
- You're already familiar with DearPyGui
- You need very specific custom rendering

### Use PySide6 Version When:
- You want native look and feel
- Platform integration is important
- You need better accessibility support
- You want standard Qt features (signals/slots)
- You prefer non-blocking UI operations
- You need better cross-platform consistency

## Core Functionality

Both implementations provide identical core features:
- ✅ Leiden to EpiDoc conversion via Claude API
- ✅ RTL language support with python-bidi
- ✅ Configurable language/script settings
- ✅ API key and model configuration
- ✅ Custom save location
- ✅ File loading and saving
- ✅ Shared configuration file (`leiden_epidoc_config.json`)

## Code Structure Comparison

### DearPyGui Approach
```python
# Immediate mode - setup all UI in one method
with dpg.window(label="Main", tag="main_window"):
    dpg.add_button(label="Convert", callback=self.convert_callback)
    dpg.add_input_text(tag="input_text", multiline=True)
    
# Access widgets by tag
text = dpg.get_value("input_text")
dpg.set_value("output_text", result)
```

### PySide6 Approach
```python
# Retained mode - create and store widget references
self.input_text = QTextEdit()
self.convert_btn = QPushButton("Convert")
self.convert_btn.clicked.connect(self.convert_text)

# Access widgets directly
text = self.input_text.toPlainText()
self.output_text.setPlainText(result)
```

## Performance Characteristics

### DearPyGui
- **Pros**: GPU-accelerated rendering, smooth animations
- **Cons**: Higher memory for font glyphs, blocking during API calls

### PySide6
- **Pros**: Efficient native rendering, threaded operations
- **Cons**: Slight overhead from Qt framework

## Migration Path

Both versions can coexist:
1. They share the same configuration file
2. Core conversion logic is identical
3. Users can run either version
4. Settings transfer between versions

To switch between versions:
```bash
# Run DearPyGui version
uv run python leiden-epidoc-dpg.py

# Run PySide6 version
uv run python leiden-epidoc-pyside.py
```

## Recommendation

**For most users**: PySide6 version is recommended due to:
- Better platform integration
- Non-blocking operations
- Native appearance
- Lower learning curve for Qt developers
- Better accessibility

**For specific needs**: DearPyGui version if you need custom rendering or are already invested in DPG ecosystem.

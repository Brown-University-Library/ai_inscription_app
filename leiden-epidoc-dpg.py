import os
import json
import re
import dearpygui.dearpygui as dpg
import anthropic
from pathlib import Path
import traceback
from leiden_prompts import SYSTEM_INSTRUCTION, EXAMPLES_TEXT
from typing import Optional, Callable
get_display: Optional[Callable[[str], str]] = None
try:
    # For RTL display shaping (visual order) in LTR widgets
    from bidi.algorithm import get_display
    HAS_BIDI = True
except Exception:
    HAS_BIDI = False

# Configuration file path
CONFIG_FILE = "leiden_epidoc_config.json"

class LeidenToEpiDocConverter:
    def __init__(self):
        self.config = self.load_config()
        self.api_key = self.config.get("api_key", "")
        self.model = self.config.get("model", "claude-sonnet-4-20250514")
        self.save_location = self.config.get("save_location", str(Path.home()))
        self.language_settings = self.config.get("language_settings", self.get_default_language_settings())
        self.last_output = ""
    
    def get_default_language_settings(self):
        """Get default language settings - basic scripts enabled by default"""
        return {
            "basic_latin": True,
            "greek": True,
            "hebrew": True,
            "arabic": False,
            "coptic": False,
            "cyrillic": False,
            "syriac": False,
            "armenian": False,
            "extended_latin": True,
            "full_bmp": False
        }
        
    def load_config(self):
        """Load configuration from file if it exists"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_config(self):
        """Save configuration to file"""
        config = {
            "api_key": self.api_key,
            "model": self.model,
            "save_location": self.save_location,
            "language_settings": self.language_settings
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    
    def get_epidoc(self, leiden) -> str:
        """Core conversion function - unchanged from original"""
        if not self.api_key:
            return "Error: API key not configured. Please set it in Settings."
        
        try:
            client = anthropic.Anthropic(api_key=self.api_key)
            
            message = client.messages.create(
                model=self.model,
                max_tokens=8192,
                temperature=0,
                system=SYSTEM_INSTRUCTION,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Below are example inputs written according to the Leiden convention and the corresponding outputs in XML following the EpiDoc convention.\n{EXAMPLES_TEXT}\n\nHere is the text in Leiden Conventions format that you need to translate: \n\n<Input>\n{leiden}\n</Input>\n"
                            }
                        ]
                    }
                ]
            )
            
            return message.content[0].text
        except Exception as e:
            return f"Error during conversion: {str(e)}\n{traceback.format_exc()}"

class LeidenEpiDocGUI:
    def __init__(self):
        self.converter = LeidenToEpiDocConverter()
        # Backing store for logical (non-bidi-reordered) input text
        self.input_logical_text: Optional[str] = None
        self.setup_gui()
    
    # --- RTL helpers ---
    @staticmethod
    def _contains_rtl(text: str) -> bool:
        if not text:
            return False
        # Hebrew (0590-05FF), Arabic (0600-06FF, 0750-077F), Syriac (0700-074F),
        # Arabic Presentation Forms (FB50-FDCF, FDF0-FDFF, FE70-FEFF)
        ranges = [
            (0x0590, 0x05FF),
            (0x0600, 0x06FF),
            (0x0700, 0x074F),
            (0x0750, 0x077F),
            (0x08A0, 0x08FF),  # Arabic Extended-A
            (0xFB50, 0xFDFF),
            (0xFE70, 0xFEFF),
        ]
        for ch in text:
            cp = ord(ch)
            for a, b in ranges:
                if a <= cp <= b:
                    return True
        return False
    
    def _bidi_visual(self, text: str) -> str:
        if not text:
            return ""
        if not HAS_BIDI:
            return text
        if not callable(get_display):  # safety if import failed
            return text
        # Only apply bidi when text likely contains RTL
        if self._contains_rtl(text):
            try:
                # type: ignore[no-any-return]
                return str(get_display(text))  # safe cast for type checker
            except Exception:
                return text
        return text
    
    def load_font_with_settings(self):
        """Load font with glyph ranges based on language settings"""
        with dpg.font_registry():
            # Try to find a font that supports Unicode
            font_paths = [
                # Linux/WSL2 paths
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
                # Windows paths
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/segoeui.ttf",
                # macOS paths
                "/System/Library/Fonts/Helvetica.ttc",
                "/Library/Fonts/Arial.ttf",
            ]
            
            default_font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        default_font = dpg.add_font(font_path, 16)
                        
                        # Load glyph ranges based on settings
                        settings = self.converter.language_settings
                        
                        # Check if full BMP is requested
                        if settings.get("full_bmp", False):
                            dpg.add_font_range(0x0020, 0xFFFF, parent=default_font)
                            print(f"Loaded font with FULL Basic Multilingual Plane")
                        else:
                            # Load individual script ranges
                            if settings.get("basic_latin", True):
                                dpg.add_font_range(0x0020, 0x00FF, parent=default_font)
                            
                            if settings.get("extended_latin", True):
                                dpg.add_font_range(0x0100, 0x024F, parent=default_font)
                                dpg.add_font_range(0x1E00, 0x1EFF, parent=default_font)
                                dpg.add_font_range(0x0300, 0x036F, parent=default_font)  # Combining marks
                            
                            if settings.get("greek", True):
                                dpg.add_font_range(0x0370, 0x03FF, parent=default_font)
                                dpg.add_font_range(0x1F00, 0x1FFF, parent=default_font)  # Greek Extended
                            
                            if settings.get("hebrew", True):
                                dpg.add_font_range(0x0590, 0x05FF, parent=default_font)
                            
                            if settings.get("arabic", False):
                                dpg.add_font_range(0x0600, 0x06FF, parent=default_font)
                                dpg.add_font_range(0x0750, 0x077F, parent=default_font)  # Arabic Supplement
                            
                            if settings.get("coptic", False):
                                dpg.add_font_range(0x2C80, 0x2CFF, parent=default_font)
                            
                            if settings.get("cyrillic", False):
                                dpg.add_font_range(0x0400, 0x04FF, parent=default_font)
                                dpg.add_font_range(0x0500, 0x052F, parent=default_font)  # Cyrillic Supplement
                            
                            if settings.get("syriac", False):
                                dpg.add_font_range(0x0700, 0x074F, parent=default_font)
                            
                            if settings.get("armenian", False):
                                dpg.add_font_range(0x0530, 0x058F, parent=default_font)
                            
                            # Always include some useful ranges
                            dpg.add_font_range(0x2000, 0x206F, parent=default_font)  # General Punctuation
                            dpg.add_font_range(0x2070, 0x209F, parent=default_font)  # Superscripts/Subscripts
                            
                            print(f"Loaded font with selected script ranges")
                        
                        print(f"Font loaded from: {font_path}")
                        break
                    except Exception as e:
                        print(f"Failed to load font from {font_path}: {e}")
                        continue
            
            if default_font:
                dpg.bind_font(default_font)
            else:
                print("No custom font found, using DearPyGUI default font")
        
    def setup_gui(self):
        dpg.create_context()
        
        # Set up font with Unicode support
        self.load_font_with_settings()
        
        # Create main window
        with dpg.window(label="Leiden to EpiDoc Converter", tag="main_window", width=1200, height=800):
            
            # Menu bar
            with dpg.menu_bar():
                with dpg.menu(label="File"):
                    dpg.add_menu_item(label="Load File", callback=self.load_file_callback)
                    dpg.add_menu_item(label="Save Output", callback=self.save_output_callback)
                    dpg.add_separator()
                    dpg.add_menu_item(label="Exit", callback=lambda: dpg.stop_dearpygui())
                
                with dpg.menu(label="Settings"):
                    dpg.add_menu_item(label="Configure API", callback=self.show_api_settings)
                    dpg.add_menu_item(label="Language/Script Support", callback=self.show_language_settings)
                    dpg.add_menu_item(label="Set Save Location", callback=self.show_save_location_settings)
                
                with dpg.menu(label="View"):
                    dpg.add_menu_item(label="Open Horizontal Scroll Viewer", callback=self.show_scroll_viewer)
            
            # Input section
            dpg.add_text("Input (Leiden Convention):")
            dpg.add_button(label="Load from File", callback=self.load_file_callback)
            dpg.add_input_text(
                tag="input_text",
                multiline=True,
                width=-1,
                height=250,
                default_value="Enter Leiden Convention text here or load from file...",
                callback=self.input_text_changed,
                on_enter=False,
                # Allow horizontal scrolling for long lines on DPG 2.1+
                no_horizontal_scroll=False
            )

            # Toggle to preview RTL in the same input box (read-only in preview)
            dpg.add_checkbox(
                label="RTL preview (read-only)",
                tag="rtl_input_preview_enabled",
                default_value=False,
                callback=self.toggle_rtl_input_preview
            )
            
            dpg.add_separator()
            
            # Convert button
            dpg.add_button(
                label="Convert to EpiDoc",
                callback=self.convert_callback,
                width=200,
                height=40
            )
            
            dpg.add_separator()
            
            # Output section
            dpg.add_text("Output (EpiDoc XML):")
            dpg.add_button(label="Save Output to File", callback=self.save_output_callback)
            dpg.add_input_text(
                tag="output_text",
                multiline=True,
                width=-1,
                height=300,
                readonly=True,
                # Allow horizontal scrolling for long lines on DPG 2.1+
                no_horizontal_scroll=False
            )
            # Ensure long lines don't soft wrap and can be scrolled horizontally where supported
            # (Kept as a no-op safety in case runtime toggling is needed on some builds)
            for _tag in ("input_text", "output_text"):
                try:
                    dpg.configure_item(_tag, no_horizontal_scroll=False)
                except Exception:
                    pass
            
            # Status bar
            dpg.add_separator()
            dpg.add_text("Ready", tag="status_text")
        
        # File dialog
        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            callback=self.file_selected_callback,
            tag="file_dialog",
            width=700,
            height=400,
            modal=True
        ):
            dpg.add_file_extension(".*")
            dpg.add_file_extension(".txt", color=(255, 255, 0, 255))
        
        # Save file dialog
        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            callback=self.save_file_callback,
            tag="save_file_dialog",
            width=700,
            height=400,
            modal=True,
            default_filename="epidoc_output.xml"
        ):
            dpg.add_file_extension(".xml", color=(0, 255, 0, 255))
            dpg.add_file_extension(".*")
        
        # Directory selector for save location
        with dpg.file_dialog(
            directory_selector=True,
            show=False,
            callback=self.directory_selected_callback,
            tag="directory_dialog",
            width=700,
            height=400,
            modal=True
        ):
            pass
        
        # Horizontal Scroll Viewer (read-only) for long lines
        with dpg.window(label="Scrollable Viewer", tag="scroll_viewer_window", width=1150, height=500, show=False, modal=False):
            dpg.add_text("Read-only viewer with horizontal scrollbars for long lines.", color=(150,150,150))
            with dpg.group(horizontal=True):
                dpg.add_button(label="Refresh", callback=self.refresh_scroll_viewer)
                dpg.add_checkbox(label="Use RTL preview for input pane", tag="scroll_viewer_rtl", default_value=False, callback=self.refresh_scroll_viewer)
            dpg.add_separator()
            with dpg.group(horizontal=True):
                with dpg.child_window(tag="scroll_input_child", width=560, height=380, border=True, autosize_x=False, autosize_y=False, horizontal_scrollbar=True):
                    dpg.add_text("Input (read-only)", color=(200,200,255))
                    dpg.add_separator()
                    dpg.add_text("", tag="scroll_input_text", wrap=0)
                with dpg.child_window(tag="scroll_output_child", width=560, height=380, border=True, autosize_x=False, autosize_y=False, horizontal_scrollbar=True):
                    dpg.add_text("Output (read-only)", color=(200,255,200))
                    dpg.add_separator()
                    dpg.add_text("", tag="scroll_output_text", wrap=0)
        
        # API Settings Window
        with dpg.window(label="API Settings", tag="api_settings_window", width=600, height=350, show=False, modal=True):
            dpg.add_text("Anthropic API Key:")
            dpg.add_input_text(
                tag="api_key_input",
                default_value=self.converter.api_key,
                password=True,
                width=-1
            )
            dpg.add_button(label="Show/Hide", callback=self.toggle_api_key_visibility)
            dpg.add_separator()
            dpg.add_text("Model Selection:")
            dpg.add_input_text(
                tag="model_input",
                default_value=self.converter.model,
                width=-1,
                hint="e.g., claude-sonnet-4-20250514"
            )
            dpg.add_text("Note: Sonnet models provide the best balance of speed and quality.", color=(150, 150, 150))
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(label="Save", callback=self.save_api_settings, width=100)
                dpg.add_button(label="Cancel", callback=lambda: dpg.hide_item("api_settings_window"), width=100)
        
        # Language Settings Window
        with dpg.window(label="Language/Script Support", tag="language_settings_window", width=700, height=600, show=False, modal=True):
            dpg.add_text("Configure Language and Script Support", color=(255, 255, 150))
            dpg.add_separator()
            dpg.add_text("Warning: Enabling more scripts increases memory usage and startup time.", color=(255, 150, 150))
            dpg.add_text("• Basic scripts: ~5MB RAM, minimal startup impact", color=(150, 150, 150))
            dpg.add_text("• All scripts: ~20-50MB RAM, 1-2 second startup delay", color=(150, 150, 150))
            dpg.add_text("• Full BMP: ~50-100MB RAM, 2-3 second startup delay", color=(150, 150, 150))
            dpg.add_separator()
            
            dpg.add_text("Essential Scripts (Recommended):")
            dpg.add_checkbox(label="Basic Latin (ASCII)", tag="lang_basic_latin", 
                           default_value=self.converter.language_settings.get("basic_latin", True))
            dpg.add_checkbox(label="Greek (including Extended/Polytonic)", tag="lang_greek",
                           default_value=self.converter.language_settings.get("greek", True))
            dpg.add_checkbox(label="Hebrew", tag="lang_hebrew",
                           default_value=self.converter.language_settings.get("hebrew", True))
            dpg.add_checkbox(label="Extended Latin (Diacritics)", tag="lang_extended_latin",
                           default_value=self.converter.language_settings.get("extended_latin", True))
            
            dpg.add_separator()
            dpg.add_text("Additional Scripts:")
            dpg.add_checkbox(label="Arabic", tag="lang_arabic",
                           default_value=self.converter.language_settings.get("arabic", False))
            dpg.add_checkbox(label="Coptic", tag="lang_coptic",
                           default_value=self.converter.language_settings.get("coptic", False))
            dpg.add_checkbox(label="Cyrillic", tag="lang_cyrillic",
                           default_value=self.converter.language_settings.get("cyrillic", False))
            dpg.add_checkbox(label="Syriac", tag="lang_syriac",
                           default_value=self.converter.language_settings.get("syriac", False))
            dpg.add_checkbox(label="Armenian", tag="lang_armenian",
                           default_value=self.converter.language_settings.get("armenian", False))
            
            dpg.add_separator()
            dpg.add_text("Maximum Coverage (High Memory Usage):")
            dpg.add_checkbox(label="Full Basic Multilingual Plane (ALL common scripts)", tag="lang_full_bmp",
                           default_value=self.converter.language_settings.get("full_bmp", False))
            
            dpg.add_separator()
            dpg.add_text("Note: Changes require application restart to take effect.", color=(255, 255, 150))
            
            with dpg.group(horizontal=True):
                dpg.add_button(label="Save", callback=self.save_language_settings, width=100)
                dpg.add_button(label="Cancel", callback=lambda: dpg.hide_item("language_settings_window"), width=100)
        
        # Save Location Settings Window
        with dpg.window(label="Save Location Settings", tag="save_location_window", width=600, height=200, show=False, modal=True):
            dpg.add_text("Default Save Location:")
            dpg.add_input_text(
                tag="save_location_input",
                default_value=self.converter.save_location,
                width=-1,
                readonly=True
            )
            dpg.add_button(label="Browse", callback=lambda: dpg.show_item("directory_dialog"))
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(label="Save", callback=self.save_location_settings, width=100)
                dpg.add_button(label="Cancel", callback=lambda: dpg.hide_item("save_location_window"), width=100)
        
        # Setup and show
        dpg.create_viewport(title="Leiden to EpiDoc Converter", width=1200, height=850)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
    
    def load_file_callback(self):
        dpg.show_item("file_dialog")
    
    def file_selected_callback(self, sender, app_data):
        selections = app_data['selections']
        if selections:
            path = list(selections.values())[0]
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Update logical store and the widget display depending on preview state
                self.input_logical_text = content
                if HAS_BIDI and dpg.get_value("rtl_input_preview_enabled"):
                    dpg.configure_item("input_text", readonly=True)
                    dpg.set_value("input_text", self._bidi_visual(content))
                else:
                    dpg.configure_item("input_text", readonly=False)
                    dpg.set_value("input_text", content)
                dpg.set_value("status_text", f"Loaded file: {path}")
            except Exception as e:
                dpg.set_value("status_text", f"Error loading file: {str(e)}")
    
    def save_output_callback(self):
        if not self.converter.last_output:
            dpg.set_value("status_text", "No output to save. Please convert text first.")
            return
        dpg.configure_item("save_file_dialog", default_path=self.converter.save_location)
        dpg.show_item("save_file_dialog")
    
    def save_file_callback(self, sender, app_data):
        path = app_data['file_path_name']
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.converter.last_output)
            dpg.set_value("status_text", f"Saved output to: {path}")
        except Exception as e:
            dpg.set_value("status_text", f"Error saving file: {str(e)}")
    
    def directory_selected_callback(self, sender, app_data):
        path = app_data['file_path_name']
        dpg.set_value("save_location_input", path)
    
    def convert_callback(self):
        # Prefer logical store; if None, fall back to current widget value
        leiden_text = self.input_logical_text if self.input_logical_text is not None else dpg.get_value("input_text")
        
        if not leiden_text or leiden_text == "Enter Leiden Convention text here or load from file...":
            dpg.set_value("status_text", "Please enter or load Leiden text first.")
            return
        
        dpg.set_value("status_text", "Converting... This may take a moment.")
        dpg.set_value("output_text", "Converting... Please wait.")
        
        # Perform conversion
        result = self.converter.get_epidoc(leiden_text)
        
        # Store the result
        self.converter.last_output = result

        # Display result (visually reorder only the text content for RTL/mixed scripts)
        display_result = self._bidi_visual_xml(result) if HAS_BIDI else result
        dpg.set_value("output_text", display_result)
        
        if "Error" in result:
            dpg.set_value("status_text", "Conversion failed. Check the output for details.")
        else:
            dpg.set_value("status_text", "Conversion complete!")
        # update viewer if open
        self.refresh_scroll_viewer()

    # --- Input (single widget) RTL preview handling ---
    def input_text_changed(self, sender, app_data):
        """Update logical store only when not in preview mode (editable)."""
        try:
            in_preview = dpg.get_value("rtl_input_preview_enabled")
        except Exception:
            in_preview = False
        if not in_preview:
            try:
                self.input_logical_text = dpg.get_value("input_text")
            except Exception:
                pass
        # keep scroll viewer in sync if visible
        self.refresh_scroll_viewer()

    def toggle_rtl_input_preview(self):
        """Switch input box between logical editable and RTL visual read-only states."""
        try:
            enabled = dpg.get_value("rtl_input_preview_enabled")
        except Exception:
            enabled = False
        # Ensure logical store is initialized
        if not self.input_logical_text:
            try:
                self.input_logical_text = dpg.get_value("input_text") or ""
            except Exception:
                self.input_logical_text = ""

        if enabled:
            if not HAS_BIDI or not callable(get_display):
                dpg.set_value("status_text", "RTL preview requires 'python-bidi'. Showing logical text.")
                dpg.configure_item("input_text", readonly=True)
                dpg.set_value("input_text", self.input_logical_text)
            else:
                dpg.configure_item("input_text", readonly=True)
                dpg.set_value("input_text", self._bidi_visual(self.input_logical_text))
        else:
            # Back to editable logical text
            dpg.configure_item("input_text", readonly=False)
            dpg.set_value("input_text", self.input_logical_text)

    # --- XML visual reorder for display-only ---
    def _bidi_visual_xml(self, xml_text: str) -> str:
        """
        For display only: run bidi visual reordering on text segments outside of XML tags,
        preserving tag order and original whitespace/formatting.
        """
        if not xml_text:
            return xml_text
        if not HAS_BIDI or not callable(get_display):
            return xml_text
        # Split into tags and text nodes
        parts = re.split(r"(<[^>]+>)", xml_text)
        for i, part in enumerate(parts):
            if not part:
                continue
            if part.startswith("<") and part.endswith(">"):
                # tag - leave as is
                continue
            # text node - apply bidi only if contains RTL
            parts[i] = self._bidi_visual(part)
        return "".join(parts)
    
    def show_api_settings(self):
        dpg.show_item("api_settings_window")
    
    def toggle_api_key_visibility(self):
        current_password = dpg.get_item_configuration("api_key_input")["password"]
        dpg.configure_item("api_key_input", password=not current_password)
    
    def save_api_settings(self):
        self.converter.api_key = dpg.get_value("api_key_input")
        self.converter.model = dpg.get_value("model_input")
        self.converter.save_config()
        dpg.hide_item("api_settings_window")
        dpg.set_value("status_text", "API settings saved.")
    
    def show_language_settings(self):
        dpg.show_item("language_settings_window")
    
    def save_language_settings(self):
        """Save language settings from checkboxes"""
        self.converter.language_settings = {
            "basic_latin": dpg.get_value("lang_basic_latin"),
            "greek": dpg.get_value("lang_greek"),
            "hebrew": dpg.get_value("lang_hebrew"),
            "extended_latin": dpg.get_value("lang_extended_latin"),
            "arabic": dpg.get_value("lang_arabic"),
            "coptic": dpg.get_value("lang_coptic"),
            "cyrillic": dpg.get_value("lang_cyrillic"),
            "syriac": dpg.get_value("lang_syriac"),
            "armenian": dpg.get_value("lang_armenian"),
            "full_bmp": dpg.get_value("lang_full_bmp")
        }
        self.converter.save_config()
        dpg.hide_item("language_settings_window")
        dpg.set_value("status_text", "Language settings saved. Restart application to apply changes.")
    
    def show_save_location_settings(self):
        dpg.show_item("save_location_window")
    
    def save_location_settings(self):
        self.converter.save_location = dpg.get_value("save_location_input")
        self.converter.save_config()
        dpg.hide_item("save_location_window")
        dpg.set_value("status_text", "Save location settings updated.")
    
    # --- Scrollable Viewer helpers ---
    def show_scroll_viewer(self):
        try:
            self.refresh_scroll_viewer()
        except Exception:
            pass
        dpg.show_item("scroll_viewer_window")

    def refresh_scroll_viewer(self):
        if not dpg.does_item_exist("scroll_viewer_window"):
            return
        if not dpg.is_item_shown("scroll_viewer_window"):
            return
        # Input side
        try:
            use_rtl = dpg.get_value("scroll_viewer_rtl") if HAS_BIDI else False
        except Exception:
            use_rtl = False
        logical = self.input_logical_text if self.input_logical_text is not None else dpg.get_value("input_text")
        input_display = self._bidi_visual(logical) if use_rtl else (logical or "")
        # Output side (apply display-only visual reorder of text nodes)
        output_display = self._bidi_visual_xml(self.converter.last_output) if HAS_BIDI else (self.converter.last_output or "")
        # Set the text (wrap=0 ensures no wrapping; child windows have horizontal scrollbars)
        try:
            dpg.set_value("scroll_input_text", input_display or "")
        except Exception:
            pass
        try:
            dpg.set_value("scroll_output_text", output_display or "")
        except Exception:
            pass
    
    def run(self):
        dpg.start_dearpygui()
        dpg.destroy_context()

if __name__ == "__main__":
    app = LeidenEpiDocGUI()
    app.run()
import os
import json
import sys
import re
import anthropic
from pathlib import Path
import traceback
from leiden_prompts import SYSTEM_INSTRUCTION, EXAMPLES_TEXT
from typing import Optional, Callable

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QMenuBar, QMenu, QFileDialog,
    QDialog, QLineEdit, QCheckBox, QFormLayout, QGroupBox, QMessageBox,
    QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QFont

get_display: Optional[Callable[[str], str]] = None
try:
    # For RTL display shaping (visual order) in LTR widgets
    from bidi.algorithm import get_display
    HAS_BIDI = True
except Exception:
    HAS_BIDI = False

# Configuration file path
CONFIG_FILE = "leiden_epidoc_config.json"


class ConversionThread(QThread):
    """Thread for running conversion without blocking UI"""
    finished = Signal(str)
    
    def __init__(self, converter, leiden_text):
        super().__init__()
        self.converter = converter
        self.leiden_text = leiden_text
    
    def run(self):
        result = self.converter.get_epidoc(self.leiden_text)
        self.finished.emit(result)


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


class APISettingsDialog(QDialog):
    """Dialog for API settings"""
    def __init__(self, parent, converter):
        super().__init__(parent)
        self.converter = converter
        self.setWindowTitle("API Settings")
        self.setModal(True)
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout()
        
        # API Key
        api_layout = QFormLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setText(self.converter.api_key)
        self.api_key_input.setEchoMode(QLineEdit.Password)
        api_layout.addRow("Anthropic API Key:", self.api_key_input)
        
        self.show_key_btn = QPushButton("Show/Hide")
        self.show_key_btn.clicked.connect(self.toggle_password)
        api_layout.addRow("", self.show_key_btn)
        
        layout.addLayout(api_layout)
        
        # Model
        model_layout = QFormLayout()
        self.model_input = QLineEdit()
        self.model_input.setText(self.converter.model)
        self.model_input.setPlaceholderText("e.g., claude-sonnet-4-20250514")
        model_layout.addRow("Model Selection:", self.model_input)
        
        note_label = QLabel("Note: Sonnet models provide the best balance of speed and quality.")
        note_label.setStyleSheet("color: gray;")
        model_layout.addRow("", note_label)
        
        layout.addLayout(model_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def toggle_password(self):
        if self.api_key_input.echoMode() == QLineEdit.Password:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)
    
    def save_settings(self):
        self.converter.api_key = self.api_key_input.text()
        self.converter.model = self.model_input.text()
        self.converter.save_config()
        self.accept()


class LanguageSettingsDialog(QDialog):
    """Dialog for language/script settings"""
    def __init__(self, parent, converter):
        super().__init__(parent)
        self.converter = converter
        self.setWindowTitle("Language/Script Support")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        
        main_layout = QVBoxLayout()
        
        # Warning text
        title = QLabel("Configure Language and Script Support")
        title.setStyleSheet("color: #FFFF96; font-weight: bold;")
        main_layout.addWidget(title)
        
        warning = QLabel("Warning: Enabling more scripts increases memory usage and startup time.")
        warning.setStyleSheet("color: #FF9696;")
        main_layout.addWidget(warning)
        
        info1 = QLabel("• Basic scripts: ~5MB RAM, minimal startup impact")
        info1.setStyleSheet("color: gray;")
        main_layout.addWidget(info1)
        
        info2 = QLabel("• All scripts: ~20-50MB RAM, 1-2 second startup delay")
        info2.setStyleSheet("color: gray;")
        main_layout.addWidget(info2)
        
        info3 = QLabel("• Full BMP: ~50-100MB RAM, 2-3 second startup delay")
        info3.setStyleSheet("color: gray;")
        main_layout.addWidget(info3)
        
        # Scroll area for checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Essential Scripts
        essential_group = QGroupBox("Essential Scripts (Recommended)")
        essential_layout = QVBoxLayout()
        
        self.checkboxes = {}
        
        self.checkboxes['basic_latin'] = QCheckBox("Basic Latin (ASCII)")
        self.checkboxes['basic_latin'].setChecked(
            self.converter.language_settings.get("basic_latin", True))
        essential_layout.addWidget(self.checkboxes['basic_latin'])
        
        self.checkboxes['greek'] = QCheckBox("Greek (including Extended/Polytonic)")
        self.checkboxes['greek'].setChecked(
            self.converter.language_settings.get("greek", True))
        essential_layout.addWidget(self.checkboxes['greek'])
        
        self.checkboxes['hebrew'] = QCheckBox("Hebrew")
        self.checkboxes['hebrew'].setChecked(
            self.converter.language_settings.get("hebrew", True))
        essential_layout.addWidget(self.checkboxes['hebrew'])
        
        self.checkboxes['extended_latin'] = QCheckBox("Extended Latin (Diacritics)")
        self.checkboxes['extended_latin'].setChecked(
            self.converter.language_settings.get("extended_latin", True))
        essential_layout.addWidget(self.checkboxes['extended_latin'])
        
        essential_group.setLayout(essential_layout)
        scroll_layout.addWidget(essential_group)
        
        # Additional Scripts
        additional_group = QGroupBox("Additional Scripts")
        additional_layout = QVBoxLayout()
        
        self.checkboxes['arabic'] = QCheckBox("Arabic")
        self.checkboxes['arabic'].setChecked(
            self.converter.language_settings.get("arabic", False))
        additional_layout.addWidget(self.checkboxes['arabic'])
        
        self.checkboxes['coptic'] = QCheckBox("Coptic")
        self.checkboxes['coptic'].setChecked(
            self.converter.language_settings.get("coptic", False))
        additional_layout.addWidget(self.checkboxes['coptic'])
        
        self.checkboxes['cyrillic'] = QCheckBox("Cyrillic")
        self.checkboxes['cyrillic'].setChecked(
            self.converter.language_settings.get("cyrillic", False))
        additional_layout.addWidget(self.checkboxes['cyrillic'])
        
        self.checkboxes['syriac'] = QCheckBox("Syriac")
        self.checkboxes['syriac'].setChecked(
            self.converter.language_settings.get("syriac", False))
        additional_layout.addWidget(self.checkboxes['syriac'])
        
        self.checkboxes['armenian'] = QCheckBox("Armenian")
        self.checkboxes['armenian'].setChecked(
            self.converter.language_settings.get("armenian", False))
        additional_layout.addWidget(self.checkboxes['armenian'])
        
        additional_group.setLayout(additional_layout)
        scroll_layout.addWidget(additional_group)
        
        # Maximum Coverage
        max_group = QGroupBox("Maximum Coverage (High Memory Usage)")
        max_layout = QVBoxLayout()
        
        self.checkboxes['full_bmp'] = QCheckBox("Full Basic Multilingual Plane (ALL common scripts)")
        self.checkboxes['full_bmp'].setChecked(
            self.converter.language_settings.get("full_bmp", False))
        max_layout.addWidget(self.checkboxes['full_bmp'])
        
        max_group.setLayout(max_layout)
        scroll_layout.addWidget(max_group)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        # Note
        note = QLabel("Note: Changes require application restart to take effect.")
        note.setStyleSheet("color: #FFFF96;")
        main_layout.addWidget(note)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def save_settings(self):
        for key, checkbox in self.checkboxes.items():
            self.converter.language_settings[key] = checkbox.isChecked()
        self.converter.save_config()
        self.accept()


class SaveLocationDialog(QDialog):
    """Dialog for save location settings"""
    def __init__(self, parent, converter):
        super().__init__(parent)
        self.converter = converter
        self.setWindowTitle("Save Location Settings")
        self.setModal(True)
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout()
        
        label = QLabel("Default Save Location:")
        layout.addWidget(label)
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setText(self.converter.save_location)
        self.path_input.setReadOnly(True)
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_directory)
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Save Location", self.converter.save_location)
        if directory:
            self.path_input.setText(directory)
    
    def save_settings(self):
        self.converter.save_location = self.path_input.text()
        self.converter.save_config()
        self.accept()


class LeidenEpiDocGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.converter = LeidenToEpiDocConverter()
        self.input_logical_text = None
        self.conversion_thread = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Leiden to EpiDoc Converter")
        self.setMinimumSize(1200, 800)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        # Input section
        input_label = QLabel("Input (Leiden Convention):")
        main_layout.addWidget(input_label)
        
        load_btn = QPushButton("Load from File")
        load_btn.clicked.connect(self.load_file)
        main_layout.addWidget(load_btn)
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter Leiden Convention text here or load from file...")
        self.input_text.setMinimumHeight(250)
        self.input_text.textChanged.connect(self.input_text_changed)
        main_layout.addWidget(self.input_text)
        
        # RTL preview checkbox
        self.rtl_preview_checkbox = QCheckBox("RTL preview (read-only)")
        self.rtl_preview_checkbox.stateChanged.connect(self.toggle_rtl_preview)
        main_layout.addWidget(self.rtl_preview_checkbox)
        
        # Convert button
        self.convert_btn = QPushButton("Convert to EpiDoc")
        self.convert_btn.setMinimumHeight(40)
        self.convert_btn.clicked.connect(self.convert_text)
        main_layout.addWidget(self.convert_btn)
        
        # Output section
        output_label = QLabel("Output (EpiDoc XML):")
        main_layout.addWidget(output_label)
        
        save_btn = QPushButton("Save Output to File")
        save_btn.clicked.connect(self.save_output)
        main_layout.addWidget(save_btn)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(300)
        main_layout.addWidget(self.output_text)
        
        # Status bar
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        central_widget.setLayout(main_layout)
    
    def create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        load_action = QAction("Load File", self)
        load_action.triggered.connect(self.load_file)
        file_menu.addAction(load_action)
        
        save_action = QAction("Save Output", self)
        save_action.triggered.connect(self.save_output)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = menu_bar.addMenu("Settings")
        
        api_action = QAction("Configure API", self)
        api_action.triggered.connect(self.show_api_settings)
        settings_menu.addAction(api_action)
        
        language_action = QAction("Language/Script Support", self)
        language_action.triggered.connect(self.show_language_settings)
        settings_menu.addAction(language_action)
        
        save_location_action = QAction("Set Save Location", self)
        save_location_action.triggered.connect(self.show_save_location_settings)
        settings_menu.addAction(save_location_action)
    
    # --- RTL helpers ---
    @staticmethod
    def _contains_rtl(text: str) -> bool:
        if not text:
            return False
        # Hebrew, Arabic, Syriac, Arabic Presentation Forms
        ranges = [
            (0x0590, 0x05FF),
            (0x0600, 0x06FF),
            (0x0700, 0x074F),
            (0x0750, 0x077F),
            (0x08A0, 0x08FF),
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
        if not HAS_BIDI or not callable(get_display):
            return text
        if self._contains_rtl(text):
            try:
                return str(get_display(text))
            except Exception:
                return text
        return text
    
    def _bidi_visual_xml(self, xml_text: str) -> str:
        """Visual reordering on text segments outside of XML tags"""
        if not xml_text:
            return xml_text
        if not HAS_BIDI or not callable(get_display):
            return xml_text
        parts = re.split(r"(<[^>]+>)", xml_text)
        for i, part in enumerate(parts):
            if not part:
                continue
            if part.startswith("<") and part.endswith(">"):
                continue
            parts[i] = self._bidi_visual(part)
        return "".join(parts)
    
    def input_text_changed(self):
        """Update logical store only when not in preview mode"""
        if not self.rtl_preview_checkbox.isChecked():
            self.input_logical_text = self.input_text.toPlainText()
    
    def toggle_rtl_preview(self):
        """Switch between logical editable and RTL visual read-only states"""
        enabled = self.rtl_preview_checkbox.isChecked()
        
        if not self.input_logical_text:
            self.input_logical_text = self.input_text.toPlainText() or ""
        
        if enabled:
            if not HAS_BIDI or not callable(get_display):
                self.status_label.setText("RTL preview requires 'python-bidi'. Showing logical text.")
                self.input_text.setReadOnly(True)
                self.input_text.setPlainText(self.input_logical_text)
            else:
                self.input_text.setReadOnly(True)
                self.input_text.setPlainText(self._bidi_visual(self.input_logical_text))
        else:
            self.input_text.setReadOnly(False)
            self.input_text.setPlainText(self.input_logical_text)
    
    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Leiden Text File", "", "Text Files (*.txt);;All Files (*)")
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.input_logical_text = content
                if HAS_BIDI and self.rtl_preview_checkbox.isChecked():
                    self.input_text.setReadOnly(True)
                    self.input_text.setPlainText(self._bidi_visual(content))
                else:
                    self.input_text.setReadOnly(False)
                    self.input_text.setPlainText(content)
                self.status_label.setText(f"Loaded file: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading file: {str(e)}")
                self.status_label.setText(f"Error loading file: {str(e)}")
    
    def save_output(self):
        if not self.converter.last_output:
            QMessageBox.warning(self, "No Output", 
                              "No output to save. Please convert text first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save EpiDoc Output", 
            os.path.join(self.converter.save_location, "epidoc_output.xml"),
            "XML Files (*.xml);;All Files (*)")
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.converter.last_output)
                self.status_label.setText(f"Saved output to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving file: {str(e)}")
                self.status_label.setText(f"Error saving file: {str(e)}")
    
    def convert_text(self):
        leiden_text = self.input_logical_text if self.input_logical_text is not None else self.input_text.toPlainText()
        
        if not leiden_text or leiden_text == "Enter Leiden Convention text here or load from file...":
            QMessageBox.warning(self, "No Input", 
                              "Please enter or load Leiden text first.")
            return
        
        self.status_label.setText("Converting... This may take a moment.")
        self.output_text.setPlainText("Converting... Please wait.")
        self.convert_btn.setEnabled(False)
        
        # Run conversion in separate thread
        self.conversion_thread = ConversionThread(self.converter, leiden_text)
        self.conversion_thread.finished.connect(self.conversion_finished)
        self.conversion_thread.start()
    
    def conversion_finished(self, result):
        self.converter.last_output = result
        
        # Display result with visual reordering for RTL
        display_result = self._bidi_visual_xml(result) if HAS_BIDI else result
        self.output_text.setPlainText(display_result)
        
        if "Error" in result:
            self.status_label.setText("Conversion failed. Check the output for details.")
        else:
            self.status_label.setText("Conversion complete!")
        
        self.convert_btn.setEnabled(True)
    
    def show_api_settings(self):
        dialog = APISettingsDialog(self, self.converter)
        if dialog.exec():
            self.status_label.setText("API settings saved.")
    
    def show_language_settings(self):
        dialog = LanguageSettingsDialog(self, self.converter)
        if dialog.exec():
            self.status_label.setText("Language settings saved. Restart application to apply changes.")
    
    def show_save_location_settings(self):
        dialog = SaveLocationDialog(self, self.converter)
        if dialog.exec():
            self.status_label.setText("Save location settings updated.")


def main():
    app = QApplication(sys.argv)
    
    # Set application-wide font for better Unicode support
    font = QFont()
    font.setPointSize(10)
    app.setFont(font)
    
    window = LeidenEpiDocGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

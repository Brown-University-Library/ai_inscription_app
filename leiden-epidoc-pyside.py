import os
import json
import sys
import anthropic
from pathlib import Path
import traceback
from leiden_prompts import SYSTEM_INSTRUCTION, EXAMPLES_TEXT

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QFileDialog,
    QDialog, QLineEdit, QFormLayout, QMessageBox
)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QAction, QFont

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
        self.last_output = ""
        
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
            "save_location": self.save_location
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    
    def get_epidoc(self, leiden) -> str:
        """Core conversion function"""
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
        self.conversion_thread = None
        self.word_wrap_enabled = True
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Leiden to EpiDoc Converter")
        self.setMinimumSize(1200, 800)
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
        self.input_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.input_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_layout.addWidget(self.input_text)
        
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
        self.output_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.output_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
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

        # View menu
        view_menu = menu_bar.addMenu("View")
        self.word_wrap_action = QAction("Word Wrap", self, checkable=True)
        self.word_wrap_action.setChecked(True)
        self.word_wrap_action.triggered.connect(self.toggle_word_wrap)
        view_menu.addAction(self.word_wrap_action)

        # Settings menu
        settings_menu = menu_bar.addMenu("Settings")
        api_action = QAction("Configure API", self)
        api_action.triggered.connect(self.show_api_settings)
        settings_menu.addAction(api_action)
        save_location_action = QAction("Set Save Location", self)
        save_location_action.triggered.connect(self.show_save_location_settings)
        settings_menu.addAction(save_location_action)

    def toggle_word_wrap(self):
        enabled = self.word_wrap_action.isChecked()
        self.word_wrap_enabled = enabled
        mode = QTextEdit.WidgetWidth if enabled else QTextEdit.NoWrap
        self.input_text.setLineWrapMode(mode)
        self.output_text.setLineWrapMode(mode)
        # Show horizontal scrollbars only if word wrap is off
        h_policy = Qt.ScrollBarAsNeeded if not enabled else Qt.ScrollBarAlwaysOff
        self.input_text.setHorizontalScrollBarPolicy(h_policy)
        self.output_text.setHorizontalScrollBarPolicy(h_policy)
    # (Removed duplicate menu creation; nothing needed here)
    
    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Leiden Text File", "", "Text Files (*.txt);;All Files (*)")
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Qt handles RTL/BiDi automatically - just set the text!
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
        leiden_text = self.input_text.toPlainText()
        
        if not leiden_text:
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
        
        # Qt handles all Unicode and BiDi automatically - just set the text!
        self.output_text.setPlainText(result)
        
        if "Error" in result:
            self.status_label.setText("Conversion failed. Check the output for details.")
        else:
            self.status_label.setText("Conversion complete!")
        
        self.convert_btn.setEnabled(True)
    
    def show_api_settings(self):
        dialog = APISettingsDialog(self, self.converter)
        if dialog.exec():
            self.status_label.setText("API settings saved.")
    
    def show_save_location_settings(self):
        dialog = SaveLocationDialog(self, self.converter)
        if dialog.exec():
            self.status_label.setText("Save location settings updated.")


def main():
    app = QApplication(sys.argv)
    
    # Set application-wide font for better Unicode support
    # Qt automatically supports all Unicode that the system fonts provide
    font = QFont()
    font.setPointSize(10)
    app.setFont(font)
    
    window = LeidenEpiDocGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

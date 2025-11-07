import os
import json
import sys
import logging
import anthropic
from pathlib import Path
import traceback
import re
from leiden_prompts import SYSTEM_INSTRUCTION, EXAMPLES_TEXT

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QFileDialog,
    QDialog, QLineEdit, QFormLayout, QMessageBox, QTabWidget, QSplitter, QInputDialog
)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QAction, QFont

# Configuration file path
CONFIG_FILE = "leiden_epidoc_config.json"


class ConversionThread(QThread):
    """Thread for running conversion without blocking UI"""
    
    finished = Signal(dict)
    
    def __init__(self, converter, leiden_text):
        super().__init__()
        self.converter = converter
        self.leiden_text = leiden_text
    
    def run(self):
        result = self.converter.get_epidoc(self.leiden_text)
        self.finished.emit(result)


class LeidenToEpiDocConverter:
    # Pre-compiled regex patterns for better performance
    ANALYSIS_PATTERN = re.compile(r'<analysis>(.*?)</analysis>', re.DOTALL | re.IGNORECASE)
    NOTES_PATTERN = re.compile(r'<notes>(.*?)</notes>', re.DOTALL | re.IGNORECASE)
    TRANSLATION_PATTERN = re.compile(r'<final_translation>(.*?)</final_translation>', re.DOTALL | re.IGNORECASE)
    
    def __init__(self):
        self.config = self.load_config()
        self.api_key = self.config.get("api_key", "")
        self.model = self.config.get("model", "claude-sonnet-4-20250514")
        self.save_location = self.config.get("save_location", str(Path.home()))
        self.last_output = ""
        # Custom prompt and examples (None means use defaults from leiden_prompts.py)
        self.custom_prompt = None
        self.custom_examples = None
        
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
    
    def get_epidoc(self, leiden) -> dict:
        """Core conversion function - returns a dict with parsed sections"""
        if not self.api_key:
            return {
                "error": "Error: API key not configured. Please set it in Settings.",
                "full_text": "Error: API key not configured. Please set it in Settings.",
                "has_tags": False
            }
        
        try:
            client = anthropic.Anthropic(api_key=self.api_key)
            
            # Use custom prompt/examples if set, otherwise use defaults
            prompt = self.custom_prompt if self.custom_prompt else SYSTEM_INSTRUCTION
            examples = self.custom_examples if self.custom_examples else EXAMPLES_TEXT
            
            # Debug logging to help troubleshoot
            logger.info(f"Using custom prompt: {self.custom_prompt is not None}")
            logger.info(f"Using custom examples: {self.custom_examples is not None}")
            if self.custom_prompt:
                logger.debug(f"Custom prompt preview: {self.custom_prompt[:50]}...")
            if self.custom_examples:
                logger.debug(f"Custom examples preview: {self.custom_examples[:50]}...")
            
            message = client.messages.create(
                model=self.model,
                max_tokens=8192,
                temperature=0,
                system=prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Below are example inputs written according to the Leiden convention and the corresponding outputs in XML following the EpiDoc convention.\n{examples}\n\nHere is the text in Leiden Conventions format that you need to translate: \n\n<Input>\n{leiden}\n</Input>\n"
                            }
                        ]
                    }
                ]
            )
            
            full_text = message.content[0].text
            return self._parse_response(full_text)
            
        except Exception as e:
            error_msg = f"Error during conversion: {str(e)}\n{traceback.format_exc()}"
            return {
                "error": error_msg,
                "full_text": error_msg,
                "has_tags": False
            }
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse the response to extract analysis, notes, and final_translation tags"""
        result = {
            "full_text": response_text,
            "has_tags": False,
            "analysis": "",
            "notes": "",
            "final_translation": "",
            "error": None
        }
        
        # Try to extract the tags using pre-compiled regex patterns
        analysis_match = self.ANALYSIS_PATTERN.search(response_text)
        notes_match = self.NOTES_PATTERN.search(response_text)
        translation_match = self.TRANSLATION_PATTERN.search(response_text)
        
        # Check if all required tags are present
        if analysis_match and notes_match and translation_match:
            result["has_tags"] = True
            result["analysis"] = analysis_match.group(1).strip()
            result["notes"] = notes_match.group(1).strip()
            result["final_translation"] = translation_match.group(1).strip()
        
        return result


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


class PromptEditorDialog(QDialog):
    """Dialog for editing and managing prompts"""
    
    def __init__(self, parent, converter):
        super().__init__(parent)
        self.converter = converter
        self.current_prompt_file = None
        self.setWindowTitle("Edit Prompt")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel("Edit the system instruction prompt for the LLM:")
        layout.addWidget(info_label)
        
        # Text editor
        self.prompt_editor = QTextEdit()
        # Use custom prompt if set, otherwise use default
        current_prompt = self.converter.custom_prompt if self.converter.custom_prompt else SYSTEM_INSTRUCTION
        self.prompt_editor.setPlainText(current_prompt)
        layout.addWidget(self.prompt_editor)
        
        # File name input
        name_layout = QHBoxLayout()
        name_label = QLabel("Prompt Name:")
        name_layout.addWidget(name_label)
        self.name_input = QLineEdit()
        self.name_input.setText("Custom Prompt")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        load_btn = QPushButton("Load Prompt")
        load_btn.clicked.connect(self.load_prompt)
        button_layout.addWidget(load_btn)
        
        save_btn = QPushButton("Save Prompt")
        save_btn.clicked.connect(self.save_prompt)
        button_layout.addWidget(save_btn)
        
        use_btn = QPushButton("Use This Prompt")
        use_btn.clicked.connect(self.use_prompt)
        button_layout.addWidget(use_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_prompt(self):
        """Load a prompt from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Prompt", "", "Text Files (*.txt);;All Files (*)")
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.prompt_editor.setPlainText(content)
                self.current_prompt_file = file_path
                # Extract name from file path
                file_name = os.path.splitext(os.path.basename(file_path))[0]
                self.name_input.setText(file_name)
                # Also set the custom prompt to be used
                self.converter.custom_prompt = content
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading prompt: {str(e)}")
    
    def save_prompt(self):
        """Save the current prompt to a file"""
        prompt_name = self.name_input.text().strip()
        if not prompt_name:
            QMessageBox.warning(self, "No Name", "Please enter a name for the prompt.")
            return
        
        # Default to .txt extension
        file_name = f"{prompt_name}.txt"
        file_path = os.path.join(self.converter.save_location, file_name)
        
        # Check if file exists
        if os.path.exists(file_path):
            reply = QMessageBox.question(
                self, "File Exists",
                f"The file '{file_name}' already exists. Do you want to overwrite it?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            
            if reply == QMessageBox.No:
                # Ask for new name
                new_name, ok = self._prompt_for_new_name(prompt_name)
                if ok and new_name:
                    prompt_name = new_name
                    file_name = f"{prompt_name}.txt"
                    file_path = os.path.join(self.converter.save_location, file_name)
                else:
                    return
            elif reply == QMessageBox.Cancel:
                return
        
        # Save the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.prompt_editor.toPlainText())
            self.current_prompt_file = file_path
            self.name_input.setText(prompt_name)
            # Also set the custom prompt to be used
            self.converter.custom_prompt = self.prompt_editor.toPlainText()
            saved_filename = os.path.basename(file_path)
            QMessageBox.information(self, "Success", f"Prompt saved as '{saved_filename}' and will be used for conversions.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving prompt: {str(e)}")
    
    def _prompt_for_new_name(self, current_name):
        """Prompt user for a new file name"""
        return QInputDialog.getText(
            self, "New Name", "Enter a new name for the prompt:", 
            QLineEdit.Normal, current_name)
    
    def use_prompt(self):
        """Use the current prompt in the converter"""
        self.converter.custom_prompt = self.prompt_editor.toPlainText()
        QMessageBox.information(self, "Success", "Prompt updated successfully!")
        self.accept()


class ExamplesEditorDialog(QDialog):
    """Dialog for editing and managing examples"""
    
    def __init__(self, parent, converter):
        super().__init__(parent)
        self.converter = converter
        self.current_examples_file = None
        self.setWindowTitle("Edit Examples")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel("Edit the example conversions for the LLM:")
        layout.addWidget(info_label)
        
        # Text editor
        self.examples_editor = QTextEdit()
        # Use custom examples if set, otherwise use default
        current_examples = self.converter.custom_examples if self.converter.custom_examples else EXAMPLES_TEXT
        self.examples_editor.setPlainText(current_examples)
        layout.addWidget(self.examples_editor)
        
        # File name input
        name_layout = QHBoxLayout()
        name_label = QLabel("Examples Name:")
        name_layout.addWidget(name_label)
        self.name_input = QLineEdit()
        self.name_input.setText("Custom Examples")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        load_btn = QPushButton("Load Examples")
        load_btn.clicked.connect(self.load_examples)
        button_layout.addWidget(load_btn)
        
        save_btn = QPushButton("Save Examples")
        save_btn.clicked.connect(self.save_examples)
        button_layout.addWidget(save_btn)
        
        use_btn = QPushButton("Use These Examples")
        use_btn.clicked.connect(self.use_examples)
        button_layout.addWidget(use_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_examples(self):
        """Load examples from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Examples", "", "Text Files (*.txt);;All Files (*)")
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.examples_editor.setPlainText(content)
                self.current_examples_file = file_path
                # Extract name from file path
                file_name = os.path.splitext(os.path.basename(file_path))[0]
                self.name_input.setText(file_name)
                # Also set the custom examples to be used
                self.converter.custom_examples = content
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading examples: {str(e)}")
    
    def save_examples(self):
        """Save the current examples to a file"""
        examples_name = self.name_input.text().strip()
        if not examples_name:
            QMessageBox.warning(self, "No Name", "Please enter a name for the examples.")
            return
        
        # Default to .txt extension
        file_name = f"{examples_name}.txt"
        file_path = os.path.join(self.converter.save_location, file_name)
        
        # Check if file exists
        if os.path.exists(file_path):
            reply = QMessageBox.question(
                self, "File Exists",
                f"The file '{file_name}' already exists. Do you want to overwrite it?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            
            if reply == QMessageBox.No:
                # Ask for new name
                new_name, ok = self._prompt_for_new_name(examples_name)
                if ok and new_name:
                    examples_name = new_name
                    file_name = f"{examples_name}.txt"
                    file_path = os.path.join(self.converter.save_location, file_name)
                else:
                    return
            elif reply == QMessageBox.Cancel:
                return
        
        # Save the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.examples_editor.toPlainText())
            self.current_examples_file = file_path
            self.name_input.setText(examples_name)
            # Also set the custom examples to be used
            self.converter.custom_examples = self.examples_editor.toPlainText()
            saved_filename = os.path.basename(file_path)
            QMessageBox.information(self, "Success", f"Examples saved as '{saved_filename}' and will be used for conversions.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving examples: {str(e)}")
    
    def _prompt_for_new_name(self, current_name):
        """Prompt user for a new file name"""
        return QInputDialog.getText(
            self, "New Name", "Enter a new name for the examples:", 
            QLineEdit.Normal, current_name)
    
    def use_examples(self):
        """Use the current examples in the converter"""
        self.converter.custom_examples = self.examples_editor.toPlainText()
        QMessageBox.information(self, "Success", "Examples updated successfully!")
        self.accept()


class LeidenEpiDocGUI(QMainWindow):
    """Main application window for Leiden to EpiDoc conversion"""
    
    # Constants for UI messages
    CONVERTING_MESSAGE = "Converting... Please wait."
    MISSING_TAGS_WARNING = ("Warning: The response from the AI did not include the expected "
                           "tags (<analysis>, <notes>, <final_translation>). "
                           "Displaying the full unseparated response in the Full Results tab.")
    
    def __init__(self):
        super().__init__()
        self.converter = LeidenToEpiDocConverter()
        self.conversion_thread = None
        self.word_wrap_enabled = True
        self.last_result = None
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
        
        # Output section with splitter
        output_label = QLabel("Output (EpiDoc XML):")
        main_layout.addWidget(output_label)
        
        # Create a horizontal splitter for the two panes
        splitter = QSplitter(Qt.Horizontal)
        
        # Left pane: Final Translation
        left_pane = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        translation_label = QLabel("Final Translation:")
        left_layout.addWidget(translation_label)
        
        save_translation_btn = QPushButton("Save Translation to File")
        save_translation_btn.clicked.connect(self.save_translation)
        left_layout.addWidget(save_translation_btn)
        
        self.translation_text = QTextEdit()
        self.translation_text.setReadOnly(True)
        self.translation_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.translation_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_layout.addWidget(self.translation_text)
        
        left_pane.setLayout(left_layout)
        splitter.addWidget(left_pane)
        
        # Right pane: Tabs for Notes, Analysis, Full Results
        right_pane = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        
        # Notes tab
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.notes_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tabs.addTab(self.notes_text, "Notes")
        
        # Analysis tab
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.analysis_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tabs.addTab(self.analysis_text, "Analysis")
        
        # Full Results tab
        self.full_results_text = QTextEdit()
        self.full_results_text.setReadOnly(True)
        self.full_results_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.full_results_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tabs.addTab(self.full_results_text, "Full Results")
        
        right_layout.addWidget(self.tabs)
        right_pane.setLayout(right_layout)
        splitter.addWidget(right_pane)
        
        # Set initial sizes for splitter (50/50 split)
        splitter.setSizes([600, 600])
        
        main_layout.addWidget(splitter)
        
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
        save_translation_action = QAction("Save Translation", self)
        save_translation_action.triggered.connect(self.save_translation)
        file_menu.addAction(save_translation_action)
        save_full_action = QAction("Save Full Output", self)
        save_full_action.triggered.connect(self.save_output)
        file_menu.addAction(save_full_action)
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
        settings_menu.addSeparator()
        edit_prompt_action = QAction("Edit Prompt", self)
        edit_prompt_action.triggered.connect(self.show_prompt_editor)
        settings_menu.addAction(edit_prompt_action)
        edit_examples_action = QAction("Edit Examples", self)
        edit_examples_action.triggered.connect(self.show_examples_editor)
        settings_menu.addAction(edit_examples_action)

    def toggle_word_wrap(self):
        enabled = self.word_wrap_action.isChecked()
        self.word_wrap_enabled = enabled
        mode = QTextEdit.WidgetWidth if enabled else QTextEdit.NoWrap
        self.input_text.setLineWrapMode(mode)
        self.translation_text.setLineWrapMode(mode)
        self.notes_text.setLineWrapMode(mode)
        self.analysis_text.setLineWrapMode(mode)
        self.full_results_text.setLineWrapMode(mode)
        # Show horizontal scrollbars only if word wrap is off
        h_policy = Qt.ScrollBarAsNeeded if not enabled else Qt.ScrollBarAlwaysOff
        self.input_text.setHorizontalScrollBarPolicy(h_policy)
        self.translation_text.setHorizontalScrollBarPolicy(h_policy)
        self.notes_text.setHorizontalScrollBarPolicy(h_policy)
        self.analysis_text.setHorizontalScrollBarPolicy(h_policy)
        self.full_results_text.setHorizontalScrollBarPolicy(h_policy)
    
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
    
    def save_translation(self):
        """Save the translation (final_translation) to a file"""
        if not self.last_result or not self.last_result.get("final_translation", "").strip():
            QMessageBox.warning(self, "No Translation", 
                              "No translation to save. Please convert text first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Translation", 
            os.path.join(self.converter.save_location, "epidoc_translation.xml"),
            "XML Files (*.xml);;All Files (*)")
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.last_result["final_translation"])
                self.status_label.setText(f"Saved translation to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving file: {str(e)}")
                self.status_label.setText(f"Error saving file: {str(e)}")
    
    def save_output(self):
        """Save the full output to a file (legacy method kept for compatibility)"""
        if not self.last_result:
            QMessageBox.warning(self, "No Output", 
                              "No output to save. Please convert text first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Full Output", 
            os.path.join(self.converter.save_location, "epidoc_output.txt"),
            "Text Files (*.txt);;All Files (*)")
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.last_result.get("full_text", ""))
                self.status_label.setText(f"Saved output to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving file: {str(e)}")
                self.status_label.setText(f"Error saving file: {str(e)}")
    
    def _clear_output_widgets(self):
        """Clear all output text widgets"""
        self.translation_text.setPlainText("")
        self.notes_text.setPlainText("")
        self.analysis_text.setPlainText("")
    
    def _set_converting_message(self):
        """Set converting message in all output widgets"""
        self.translation_text.setPlainText(self.CONVERTING_MESSAGE)
        self.notes_text.setPlainText(self.CONVERTING_MESSAGE)
        self.analysis_text.setPlainText(self.CONVERTING_MESSAGE)
        self.full_results_text.setPlainText(self.CONVERTING_MESSAGE)
    
    def convert_text(self):
        leiden_text = self.input_text.toPlainText()
        
        if not leiden_text:
            QMessageBox.warning(self, "No Input", 
                              "Please enter or load Leiden text first.")
            return
        
        self.status_label.setText("Converting... This may take a moment.")
        self._set_converting_message()
        self.convert_btn.setEnabled(False)
        
        # Run conversion in separate thread
        self.conversion_thread = ConversionThread(self.converter, leiden_text)
        self.conversion_thread.finished.connect(self.conversion_finished)
        self.conversion_thread.start()
    
    def conversion_finished(self, result):
        """Handle the conversion result and update the UI"""
        self.last_result = result
        self.converter.last_output = result.get("full_text", "")
        
        # Check if there was an error
        if result.get("error"):
            self._clear_output_widgets()
            self.full_results_text.setPlainText(result["error"])
            self.tabs.setCurrentIndex(2)  # Switch to "Full Results" tab
            self.status_label.setText("Conversion failed. Check the Full Results tab for details.")
            self.convert_btn.setEnabled(True)
            return
        
        # Check if the response has the required tags
        if result["has_tags"]:
            # Display parsed sections
            self.translation_text.setPlainText(result["final_translation"])
            self.notes_text.setPlainText(result["notes"])
            self.analysis_text.setPlainText(result["analysis"])
            self.full_results_text.setPlainText(result["full_text"])
            self.status_label.setText("Conversion complete!")
        else:
            # Missing tags - display warning and show full results
            QMessageBox.warning(self, "Missing Tags", self.MISSING_TAGS_WARNING)
            
            self._clear_output_widgets()
            self.full_results_text.setPlainText(result["full_text"])
            self.tabs.setCurrentIndex(2)  # Switch to "Full Results" tab
            self.status_label.setText("Warning: Missing tags. See Full Results tab.")
        
        self.convert_btn.setEnabled(True)
    
    def show_api_settings(self):
        dialog = APISettingsDialog(self, self.converter)
        if dialog.exec():
            self.status_label.setText("API settings saved.")
    
    def show_save_location_settings(self):
        dialog = SaveLocationDialog(self, self.converter)
        if dialog.exec():
            self.status_label.setText("Save location settings updated.")
    
    def show_prompt_editor(self):
        """Show the prompt editor dialog"""
        dialog = PromptEditorDialog(self, self.converter)
        if dialog.exec():
            self.status_label.setText("Prompt settings updated.")
    
    def show_examples_editor(self):
        """Show the examples editor dialog"""
        dialog = ExamplesEditorDialog(self, self.converter)
        if dialog.exec():
            self.status_label.setText("Examples settings updated.")


def main():
    app = QApplication(sys.argv)
    
    font = QFont()
    font.setPointSize(10)
    app.setFont(font)
    
    window = LeidenEpiDocGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

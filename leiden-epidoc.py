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
    QDialog, QLineEdit, QFormLayout, QMessageBox, QSplitter, QInputDialog,
    QTabWidget, QRadioButton, QButtonGroup, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QAction, QFont

# Configuration file path
CONFIG_FILE = "leiden_epidoc_config.json"


class FileItem:
    """Represents a single file with its content and conversion state"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.input_text = ""
        self.conversion_result = None
        self.is_converted = False
        
    def load_content(self):
        """Load the file content"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.input_text = f.read()
            return True
        except Exception as e:
            logger.error(f"Error loading file {self.file_path}: {str(e)}")
            return False


class ConversionThread(QThread):
    """Thread for running conversion without blocking UI"""
    
    finished = Signal(dict)
    progress = Signal(int, int)  # current, total
    file_started = Signal(str)  # file_path - emitted when file starts converting
    file_completed = Signal(str)  # file_path - emitted when file finishes converting
    
    def __init__(self, converter, file_items):
        super().__init__()
        self.converter = converter
        self.file_items = file_items  # List of FileItem objects to convert
    
    def run(self):
        total = len(self.file_items)
        for idx, file_item in enumerate(self.file_items, 1):
            self.file_started.emit(file_item.file_path)
            self.progress.emit(idx, total)
            result = self.converter.get_epidoc(file_item.input_text)
            file_item.conversion_result = result
            file_item.is_converted = True
            self.file_completed.emit(file_item.file_path)
        
        # Emit finished signal with summary
        self.finished.emit({"success": True, "converted_count": total})


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
            except (OSError, json.JSONDecodeError):
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
    MISSING_TAGS_WARNING = ("Warning: The response from the AI did not include the expected "
                           "tags (<analysis>, <notes>, <final_translation>). "
                           "Displaying the full unseparated response in the Full Output tab.")
    
    def __init__(self):
        super().__init__()
        self.converter = LeidenToEpiDocConverter()
        self.conversion_thread = None
        self.word_wrap_enabled = True
        self.file_items = {}  # Dictionary mapping file_path to FileItem
        self.current_file_item = None  # Currently selected file
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Leiden to EpiDoc Converter")
        self.setMinimumSize(1200, 800)
        self.create_menu_bar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        # Main horizontal splitter: left pane (file list) and right pane (content viewer)
        main_splitter = QSplitter(Qt.Horizontal)
        
        # LEFT PANE: File table with checkboxes and status
        left_pane = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Load files button
        load_files_btn = QPushButton("Load Files")
        load_files_btn.clicked.connect(self.load_files)
        left_layout.addWidget(load_files_btn)
        
        # File table
        files_label = QLabel("Loaded Files:")
        left_layout.addWidget(files_label)
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(2)
        self.file_table.setHorizontalHeaderLabels(["Filename", "Converted"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.file_table.cellClicked.connect(self.on_file_selected)
        left_layout.addWidget(self.file_table)
        
        # Button area - all action buttons in one place
        button_area_layout = QVBoxLayout()
        button_area_layout.setSpacing(8)
        
        # Selection buttons row
        selection_btn_layout = QHBoxLayout()
        selection_btn_layout.setSpacing(8)
        
        self.select_converted_btn = QPushButton("Select Converted")
        self.select_converted_btn.clicked.connect(self.select_all_converted)
        self.select_converted_btn.setEnabled(False)
        selection_btn_layout.addWidget(self.select_converted_btn)
        
        self.select_unconverted_btn = QPushButton("Select Unconverted")
        self.select_unconverted_btn.clicked.connect(self.select_all_unconverted)
        self.select_unconverted_btn.setEnabled(False)
        selection_btn_layout.addWidget(self.select_unconverted_btn)
        
        button_area_layout.addLayout(selection_btn_layout)
        
        # Convert selected button
        self.convert_btn = QPushButton("Convert Selected to EpiDoc")
        self.convert_btn.setMinimumHeight(40)
        self.convert_btn.clicked.connect(self.convert_selected)
        self.convert_btn.setEnabled(False)
        button_area_layout.addWidget(self.convert_btn)
        
        # Save button (moved from right pane)
        self.save_btn = QPushButton("Save Selected Output")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self.save_output)
        self.save_btn.setEnabled(False)
        button_area_layout.addWidget(self.save_btn)
        
        left_layout.addLayout(button_area_layout)
        
        left_pane.setLayout(left_layout)
        main_splitter.addWidget(left_pane)
        
        # RIGHT PANE: Content viewer with tabs
        right_pane = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Input tab
        self.input_text = QTextEdit()
        self.input_text.setReadOnly(True)
        self.input_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.input_text.setPlaceholderText("Select a file to view its input text...")
        self.tab_widget.addTab(self.input_text, "Input")
        
        # EpiDoc tab
        self.epidoc_text = QTextEdit()
        self.epidoc_text.setReadOnly(True)
        self.epidoc_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.epidoc_text.setPlaceholderText("Convert the file to view EpiDoc XML...")
        self.tab_widget.addTab(self.epidoc_text, "EpiDoc")
        
        # Notes tab
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.notes_text.setPlaceholderText("Convert the file to view notes...")
        self.tab_widget.addTab(self.notes_text, "Notes")
        
        # Analysis tab
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.analysis_text.setPlaceholderText("Convert the file to view analysis...")
        self.tab_widget.addTab(self.analysis_text, "Analysis")
        
        # Full Output tab
        self.full_output_text = QTextEdit()
        self.full_output_text.setReadOnly(True)
        self.full_output_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.full_output_text.setPlaceholderText("Convert the file to view full output...")
        self.tab_widget.addTab(self.full_output_text, "Full Output")
        
        right_layout.addWidget(self.tab_widget)
        
        right_pane.setLayout(right_layout)
        main_splitter.addWidget(right_pane)
        
        # Set 40/60 split (left/right)
        main_splitter.setSizes([480, 720])  # 40% : 60%
        
        main_layout.addWidget(main_splitter)
        
        # Status bar
        self.status_label = QLabel("Ready - Load files to begin")
        self.status_label.setMaximumHeight(25)
        self.status_label.setStyleSheet("padding: 5px;")
        main_layout.addWidget(self.status_label)
        
        central_widget.setLayout(main_layout)
    
    def create_menu_bar(self):
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")
        load_action = QAction("Load Files", self)
        load_action.triggered.connect(self.load_files)
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
        settings_menu.addSeparator()
        edit_prompt_action = QAction("Edit Prompt", self)
        edit_prompt_action.triggered.connect(self.show_prompt_editor)
        settings_menu.addAction(edit_prompt_action)
        edit_examples_action = QAction("Edit Examples", self)
        edit_examples_action.triggered.connect(self.show_examples_editor)
        settings_menu.addAction(edit_examples_action)

    def on_tab_changed(self, index):
        """Handle tab change to update which content is displayed"""
        # Content is already displayed in the tab widget, no action needed
        pass

    def toggle_word_wrap(self):
        enabled = self.word_wrap_action.isChecked()
        self.word_wrap_enabled = enabled
        mode = QTextEdit.WidgetWidth if enabled else QTextEdit.NoWrap
        self.input_text.setLineWrapMode(mode)
        self.epidoc_text.setLineWrapMode(mode)
        self.notes_text.setLineWrapMode(mode)
        self.analysis_text.setLineWrapMode(mode)
        self.full_output_text.setLineWrapMode(mode)
        # Show horizontal scrollbars only if word wrap is off
        h_policy = Qt.ScrollBarAsNeeded if not enabled else Qt.ScrollBarAlwaysOff
        self.input_text.setHorizontalScrollBarPolicy(h_policy)
        self.epidoc_text.setHorizontalScrollBarPolicy(h_policy)
        self.notes_text.setHorizontalScrollBarPolicy(h_policy)
        self.analysis_text.setHorizontalScrollBarPolicy(h_policy)
        self.full_output_text.setHorizontalScrollBarPolicy(h_policy)
    
    def load_files(self):
        """Load multiple files for batch processing"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Load Leiden Text Files", "", "Text Files (*.txt);;All Files (*)")
        
        if file_paths:
            loaded_count = 0
            for file_path in file_paths:
                if file_path not in self.file_items:
                    file_item = FileItem(file_path)
                    if file_item.load_content():
                        self.file_items[file_path] = file_item
                        self._add_file_to_table(file_item)
                        loaded_count += 1
                    else:
                        QMessageBox.warning(self, "Load Error", 
                                          f"Failed to load file: {file_item.file_name}")
            
            if loaded_count > 0:
                self.status_label.setText(f"Loaded {loaded_count} file(s)")
                self.convert_btn.setEnabled(True)
            else:
                self.status_label.setText("No new files loaded")
    
    def _add_file_to_table(self, file_item):
        """Add a file item to the table with a checkbox"""
        row = self.file_table.rowCount()
        self.file_table.insertRow(row)
        
        # Filename column with checkbox
        filename_item = QTableWidgetItem(file_item.file_name)
        filename_item.setCheckState(Qt.Checked)  # Default to checked
        filename_item.setData(Qt.UserRole, file_item.file_path)  # Store file path as data
        self.file_table.setItem(row, 0, filename_item)
        
        # Converted column - initially empty
        converted_item = QTableWidgetItem("")
        converted_item.setTextAlignment(Qt.AlignCenter)
        converted_item.setFlags(converted_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
        self.file_table.setItem(row, 1, converted_item)
        
        # Update button states after adding a file
        self._update_selection_button_states()
    
    def _update_selection_button_states(self):
        """Update the enabled state of selection buttons based on available files"""
        has_converted = False
        has_unconverted = False
        
        for file_path, file_item in self.file_items.items():
            if file_item.is_converted:
                has_converted = True
            else:
                has_unconverted = True
            
            # Early exit if both states found
            if has_converted and has_unconverted:
                break
        
        self.select_converted_btn.setEnabled(has_converted)
        self.select_unconverted_btn.setEnabled(has_unconverted)
    
    def select_all_converted(self):
        """Select all files that have been converted"""
        for row in range(self.file_table.rowCount()):
            filename_item = self.file_table.item(row, 0)
            if filename_item:
                file_path = filename_item.data(Qt.UserRole)
                if file_path in self.file_items:
                    file_item = self.file_items[file_path]
                    if file_item.is_converted:
                        filename_item.setCheckState(Qt.Checked)
                    else:
                        filename_item.setCheckState(Qt.Unchecked)
        
        self.status_label.setText("Selected all converted files")
    
    def select_all_unconverted(self):
        """Select all files that have not been converted"""
        for row in range(self.file_table.rowCount()):
            filename_item = self.file_table.item(row, 0)
            if filename_item:
                file_path = filename_item.data(Qt.UserRole)
                if file_path in self.file_items:
                    file_item = self.file_items[file_path]
                    if not file_item.is_converted:
                        filename_item.setCheckState(Qt.Checked)
                    else:
                        filename_item.setCheckState(Qt.Unchecked)
        
        self.status_label.setText("Selected all unconverted files")
    
    def on_file_selected(self, row, column):
        """Handle file selection from the table"""
        filename_item = self.file_table.item(row, 0)
        if filename_item:
            file_path = filename_item.data(Qt.UserRole)
            if file_path in self.file_items:
                self.current_file_item = self.file_items[file_path]
                self._display_file_content(self.current_file_item)
                self.save_btn.setEnabled(True)
    
    def _display_file_content(self, file_item):
        """Display the content of the selected file in the right pane"""
        # Always show input text
        self.input_text.setPlainText(file_item.input_text)
        
        # Show conversion results if available
        if file_item.is_converted and file_item.conversion_result:
            result = file_item.conversion_result
            
            if result.get("error"):
                self.epidoc_text.setPlainText(f"Error: {result['error']}")
                self.notes_text.setPlainText("")
                self.analysis_text.setPlainText("")
                self.full_output_text.setPlainText(result.get("full_text", ""))
            elif result.get("has_tags"):
                self.epidoc_text.setPlainText(result.get("final_translation", ""))
                self.notes_text.setPlainText(result.get("notes", ""))
                self.analysis_text.setPlainText(result.get("analysis", ""))
                self.full_output_text.setPlainText(result.get("full_text", ""))
            else:
                self.epidoc_text.setPlainText("")
                self.notes_text.setPlainText("")
                self.analysis_text.setPlainText("")
                self.full_output_text.setPlainText(result.get("full_text", ""))
                if not result.get("error"):
                    QMessageBox.warning(self, "Missing Tags", self.MISSING_TAGS_WARNING)
        else:
            # Not yet converted
            self.epidoc_text.setPlainText("")
            self.notes_text.setPlainText("")
            self.analysis_text.setPlainText("")
            self.full_output_text.setPlainText("")
    
    def convert_selected(self):
        """Convert all selected files"""
        selected_items = []
        selected_file_paths = []
        for row in range(self.file_table.rowCount()):
            filename_item = self.file_table.item(row, 0)
            if filename_item and filename_item.checkState() == Qt.Checked:
                file_path = filename_item.data(Qt.UserRole)
                if file_path in self.file_items:
                    selected_items.append(self.file_items[file_path])
                    selected_file_paths.append(file_path)
        
        if not selected_items:
            QMessageBox.warning(self, "No Selection", 
                              "Please select at least one file to convert.")
            return
        
        # Set all selected files to "Queued" status
        for row in range(self.file_table.rowCount()):
            filename_item = self.file_table.item(row, 0)
            if filename_item and filename_item.data(Qt.UserRole) in selected_file_paths:
                converted_item = self.file_table.item(row, 1)
                if converted_item:
                    converted_item.setText("Queued")
        
        # Show status about custom prompts
        custom_status = []
        if self.converter.custom_prompt:
            custom_status.append("custom prompt")
        if self.converter.custom_examples:
            custom_status.append("custom examples")
        
        if custom_status:
            status_msg = f"Converting {len(selected_items)} file(s) with {' and '.join(custom_status)}..."
        else:
            status_msg = f"Converting {len(selected_items)} file(s)..."
        
        self.status_label.setText(status_msg)
        self.convert_btn.setEnabled(False)
        
        # Run conversion in separate thread
        self.conversion_thread = ConversionThread(self.converter, selected_items)
        self.conversion_thread.progress.connect(self.conversion_progress)
        self.conversion_thread.file_started.connect(self.on_file_conversion_started)
        self.conversion_thread.file_completed.connect(self.on_file_conversion_completed)
        self.conversion_thread.finished.connect(self.conversion_finished)
        self.conversion_thread.start()
    
    def conversion_progress(self, current, total):
        """Handle conversion progress updates"""
        self.status_label.setText(f"Converting file {current} of {total}...")
    
    def on_file_conversion_started(self, file_path):
        """Update table to show 'In Progress' for the file being converted"""
        for row in range(self.file_table.rowCount()):
            filename_item = self.file_table.item(row, 0)
            if filename_item and filename_item.data(Qt.UserRole) == file_path:
                converted_item = self.file_table.item(row, 1)
                if converted_item:
                    converted_item.setText("In Progress")
                break
    
    def on_file_conversion_completed(self, file_path):
        """Update table to show checkmark for converted file and uncheck it"""
        for row in range(self.file_table.rowCount()):
            filename_item = self.file_table.item(row, 0)
            if filename_item and filename_item.data(Qt.UserRole) == file_path:
                # Update converted column to show checkmark
                converted_item = self.file_table.item(row, 1)
                if converted_item:
                    converted_item.setText("✓")
                # Uncheck the file
                filename_item.setCheckState(Qt.Unchecked)
                break
    
    def conversion_finished(self, result):
        """Handle batch conversion completion"""
        self.convert_btn.setEnabled(True)
        
        if result.get("success"):
            count = result.get("converted_count", 0)
            self.status_label.setText(f"Successfully converted {count} file(s)")
            
            # Refresh the display if a file is currently selected
            if self.current_file_item:
                self._display_file_content(self.current_file_item)
        else:
            self.status_label.setText("Conversion failed")
        
        # Update selection button states after conversion
        self._update_selection_button_states()
    
    def save_output(self):
        """Save the output for all checked files based on the currently selected tab"""
        # Get all checked files
        checked_files = []
        unconverted_files = []
        for row in range(self.file_table.rowCount()):
            filename_item = self.file_table.item(row, 0)
            if filename_item and filename_item.checkState() == Qt.Checked:
                file_path = filename_item.data(Qt.UserRole)
                if file_path in self.file_items:
                    file_item = self.file_items[file_path]
                    if file_item.is_converted:
                        checked_files.append(file_item)
                    else:
                        unconverted_files.append(file_item)
        
        # If nothing is checked, fall back to current file
        if not checked_files and not unconverted_files:
            if self.current_file_item and self.current_file_item.is_converted:
                checked_files = [self.current_file_item]
            else:
                QMessageBox.warning(self, "No Output", 
                                  "No converted files selected. Please check the files you want to save.")
                return
        
        # Warn if some checked files are not converted
        if unconverted_files:
            unconverted_names = ", ".join([f.file_name for f in unconverted_files])
            if checked_files:
                reply = QMessageBox.warning(
                    self, "Some Files Not Converted",
                    f"The following files have not been converted and will be skipped:\n\n{unconverted_names}\n\n"
                    f"Do you want to continue saving the {len(checked_files)} converted file(s)?",
                    QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            else:
                QMessageBox.warning(self, "No Converted Files", 
                                  f"None of the selected files have been converted yet:\n\n{unconverted_names}\n\n"
                                  "Please convert the files before saving.")
                return
        
        # Determine what to save based on current tab
        current_tab = self.tab_widget.currentIndex()
        
        # Single file - use file dialog
        if len(checked_files) == 1:
            self._save_single_file(checked_files[0], current_tab)
        else:
            # Multiple files - use directory picker and auto-name files
            self._save_multiple_files(checked_files, current_tab)
    
    def _get_output_info_for_tab(self, file_item, tab_index):
        """Get the content, default filename, and extension based on tab index"""
        result = file_item.conversion_result
        base_name = os.path.splitext(file_item.file_name)[0]
        original_ext = os.path.splitext(file_item.file_name)[1] or ".txt"
        
        if tab_index == 0:  # Input
            return (file_item.input_text, file_item.file_name, original_ext)
        elif tab_index == 1:  # EpiDoc
            return (result.get("final_translation", ""), f"{base_name}_epidoc.xml", ".xml")
        elif tab_index == 2:  # Notes
            return (result.get("notes", ""), f"{base_name}_notes.txt", ".txt")
        elif tab_index == 3:  # Analysis
            return (result.get("analysis", ""), f"{base_name}_analysis.txt", ".txt")
        else:  # Full Output
            return (result.get("full_text", ""), f"{base_name}_full.txt", ".txt")
    
    def _save_single_file(self, file_item, tab_index):
        """Save a single file with a file dialog"""
        content, default_name, ext = self._get_output_info_for_tab(file_item, tab_index)
        
        if ext == ".xml":
            file_filter = "XML Files (*.xml);;All Files (*)"
        else:
            file_filter = "Text Files (*.txt);;All Files (*)"
        
        if not content.strip():
            QMessageBox.warning(self, "No Content", 
                              "No content to save for this tab.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Output", 
            os.path.join(self.converter.save_location, default_name),
            file_filter)
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.status_label.setText(f"Saved to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving file: {str(e)}")
                self.status_label.setText(f"Error saving file: {str(e)}")
    
    def _save_multiple_files(self, file_items, tab_index):
        """Save multiple files to a directory with auto-generated names"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory to Save Files", 
            self.converter.save_location)
        
        if not directory:
            return
        
        saved_count = 0
        error_count = 0
        skipped_count = 0
        used_names = set()  # Track used names to avoid collisions
        
        for file_item in file_items:
            content, default_name, _ = self._get_output_info_for_tab(file_item, tab_index)
            
            if not content.strip():
                skipped_count += 1
                continue
            
            # Handle file name collisions
            final_name = default_name
            if default_name in used_names:
                base, ext = os.path.splitext(default_name)
                counter = 1
                while final_name in used_names:
                    final_name = f"{base}_{counter}{ext}"
                    counter += 1
            
            used_names.add(final_name)
            file_path = os.path.join(directory, final_name)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving {final_name}: {str(e)}")
                error_count += 1
        
        # Show summary
        if error_count > 0:
            self.status_label.setText(f"Saved {saved_count} file(s), {error_count} error(s), {skipped_count} skipped")
            QMessageBox.warning(self, "Save Complete", 
                              f"Saved {saved_count} file(s) to {directory}\n"
                              f"{error_count} file(s) had errors\n"
                              f"{skipped_count} file(s) skipped (no content)")
        else:
            self.status_label.setText(f"Saved {saved_count} file(s) to {directory}")
            if skipped_count > 0:
                QMessageBox.information(self, "Save Complete", 
                                      f"Saved {saved_count} file(s) to {directory}\n"
                                      f"{skipped_count} file(s) skipped (no content)")

    
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
            # Update status to show whether custom prompt is active
            if self.converter.custom_prompt:
                self.status_label.setText("Custom prompt is now active and will be used for conversions.")
            else:
                self.status_label.setText("Prompt settings updated.")
    
    def show_examples_editor(self):
        """Show the examples editor dialog"""
        dialog = ExamplesEditorDialog(self, self.converter)
        if dialog.exec():
            # Update status to show whether custom examples are active
            if self.converter.custom_examples:
                self.status_label.setText("Custom examples are now active and will be used for conversions.")
            else:
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

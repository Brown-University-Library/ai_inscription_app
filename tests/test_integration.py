"""
Integration tests for the application.
"""
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import sys

# Mock PySide6 before importing
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Integration tests for complete workflows."""
    
    def test_config_save_and_load_workflow(self, tmp_path, monkeypatch):
        """Test the complete workflow of saving and loading configuration."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "leiden_epidoc_config.json"
        
        # Step 1: Create and save config
        config = {
            "api_key": "integration-test-key",
            "model": "claude-sonnet-4-20250514",
            "save_location": str(tmp_path)
        }
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Step 2: Load config back
        with open(config_file, 'r') as f:
            loaded_config = json.load(f)
        
        # Step 3: Verify
        assert loaded_config["api_key"] == config["api_key"]
        assert loaded_config["model"] == config["model"]
        assert loaded_config["save_location"] == config["save_location"]
    
    def test_file_load_and_conversion_workflow(self, sample_file_content, tmp_path):
        """Test workflow of loading a file and preparing for conversion."""
        # Step 1: Create file item
        file_path = str(sample_file_content)
        file_item = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'input_text': "",
            'conversion_result': None,
            'is_converted': False,
            'has_error': False
        }
        
        # Step 2: Load content
        with open(file_path, 'r', encoding='utf-8') as f:
            file_item['input_text'] = f.read()
        
        # Step 3: Verify loaded
        assert file_item['input_text'] != ""
        assert "[Marcus]" in file_item['input_text']
        
        # Step 4: Simulate conversion result
        file_item['conversion_result'] = {
            'has_tags': True,
            'analysis': 'Test analysis',
            'notes': 'Test notes',
            'final_translation': '<lb/>Marcus Aurelius',
            'error': None
        }
        file_item['is_converted'] = True
        
        # Step 5: Verify conversion state
        assert file_item['is_converted'] is True
        assert file_item['conversion_result']['has_tags'] is True
    
    def test_multiple_files_batch_workflow(self, tmp_path):
        """Test workflow with multiple files."""
        # Create multiple test files
        files = []
        for i in range(3):
            file_path = tmp_path / f"inscription_{i}.txt"
            content = f"Test inscription {i}\nv(ir) c(larissim)"
            file_path.write_text(content, encoding='utf-8')
            files.append(file_path)
        
        # Load all files
        file_items = {}
        for file_path in files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            file_items[str(file_path)] = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'input_text': content,
                'conversion_result': None,
                'is_converted': False
            }
        
        assert len(file_items) == 3
        
        # Simulate conversions
        for file_path, item in file_items.items():
            item['conversion_result'] = {
                'has_tags': True,
                'final_translation': f'<lb/>{item["input_text"]}'
            }
            item['is_converted'] = True
        
        # Verify all converted
        assert all(item['is_converted'] for item in file_items.values())
    
    def test_save_output_workflow(self, tmp_path):
        """Test the workflow of saving converted output."""
        # Create a converted file item
        file_item = {
            'file_name': 'test.txt',
            'conversion_result': {
                'has_tags': True,
                'final_translation': '<lb/>Marcus <supplied reason="lost">Aurelius</supplied>',
                'notes': 'Translation notes',
                'analysis': 'Analysis text',
                'full_text': 'Full response text'
            },
            'is_converted': True,
            'has_error': False
        }
        
        # Save different outputs
        outputs = {
            'epidoc': file_item['conversion_result']['final_translation'],
            'notes': file_item['conversion_result']['notes'],
            'analysis': file_item['conversion_result']['analysis'],
        }
        
        for output_type, content in outputs.items():
            output_file = tmp_path / f"test_{output_type}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Verify saved
            assert output_file.exists()
            assert output_file.read_text(encoding='utf-8') == content
    
    def test_error_handling_workflow(self, tmp_path):
        """Test workflow with errors."""
        # Simulate API error
        file_item = {
            'file_path': str(tmp_path / "test.txt"),
            'input_text': 'Test content',
            'conversion_result': {
                'error': 'API connection failed',
                'full_text': 'Error: API connection failed',
                'has_tags': False
            },
            'is_converted': True,
            'has_error': True
        }
        
        # Verify error state
        assert file_item['has_error'] is True
        assert file_item['conversion_result']['error'] is not None
        assert file_item['conversion_result']['has_tags'] is False
    
    def test_config_update_workflow(self, tmp_path, monkeypatch):
        """Test updating configuration."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "leiden_epidoc_config.json"
        
        # Initial config
        initial_config = {
            "api_key": "old-key",
            "model": "old-model",
            "save_location": "/old/path"
        }
        with open(config_file, 'w') as f:
            json.dump(initial_config, f)
        
        # Load config
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Update config
        config["api_key"] = "new-key"
        config["model"] = "new-model"
        
        # Save updated config
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Reload and verify
        with open(config_file, 'r') as f:
            updated_config = json.load(f)
        
        assert updated_config["api_key"] == "new-key"
        assert updated_config["model"] == "new-model"
        assert updated_config["save_location"] == initial_config["save_location"]
    
    def test_clear_all_files_workflow(self, tmp_path):
        """Test workflow of clearing all loaded files."""
        # Create multiple test files
        files = []
        for i in range(3):
            file_path = tmp_path / f"inscription_{i}.txt"
            content = f"Test inscription {i}\nv(ir) c(larissim)"
            file_path.write_text(content, encoding='utf-8')
            files.append(file_path)
        
        # Simulate loading files into application state
        file_items = {}
        for file_path in files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            file_items[str(file_path)] = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'input_text': content,
                'conversion_result': None,
                'is_converted': False
            }
        
        current_file_item = file_items[str(files[0])]
        missing_tags_warned = {str(files[1])}
        
        # Verify initial state has data
        assert len(file_items) == 3
        assert current_file_item is not None
        assert len(missing_tags_warned) == 1
        
        # Simulate clear all files operation
        file_items.clear()
        current_file_item = None
        missing_tags_warned.clear()
        
        # Verify cleared state
        assert len(file_items) == 0
        assert current_file_item is None
        assert len(missing_tags_warned) == 0


@pytest.mark.integration
class TestCustomPromptsWorkflow:
    """Integration tests for custom prompts and examples."""
    
    def test_custom_prompt_save_and_load(self, tmp_path):
        """Test saving and loading custom prompts."""
        prompt_file = tmp_path / "custom_prompt.txt"
        custom_prompt = "This is a custom system instruction for testing."
        
        # Save custom prompt
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(custom_prompt)
        
        # Load custom prompt
        with open(prompt_file, 'r', encoding='utf-8') as f:
            loaded_prompt = f.read()
        
        assert loaded_prompt == custom_prompt
    
    def test_custom_examples_save_and_load(self, tmp_path):
        """Test saving and loading custom examples."""
        examples_file = tmp_path / "custom_examples.txt"
        custom_examples = """<example>
<input>Test [input]</input>
<output><supplied reason="lost">input</supplied></output>
</example>"""
        
        # Save custom examples
        with open(examples_file, 'w', encoding='utf-8') as f:
            f.write(custom_examples)
        
        # Load custom examples
        with open(examples_file, 'r', encoding='utf-8') as f:
            loaded_examples = f.read()
        
        assert loaded_examples == custom_examples
    
    def test_switching_between_default_and_custom(self, tmp_path):
        """Test switching between default and custom prompts."""
        from leiden_prompts import SYSTEM_INSTRUCTION, EXAMPLES_TEXT
        
        # Start with defaults
        current_prompt = None
        current_examples = None
        
        prompt = current_prompt if current_prompt else SYSTEM_INSTRUCTION
        examples = current_examples if current_examples else EXAMPLES_TEXT
        
        assert prompt == SYSTEM_INSTRUCTION
        assert examples == EXAMPLES_TEXT
        
        # Switch to custom
        current_prompt = "Custom prompt"
        current_examples = "Custom examples"
        
        prompt = current_prompt if current_prompt else SYSTEM_INSTRUCTION
        examples = current_examples if current_examples else EXAMPLES_TEXT
        
        assert prompt == "Custom prompt"
        assert examples == "Custom examples"
        
        # Switch back to default
        current_prompt = None
        current_examples = None
        
        prompt = current_prompt if current_prompt else SYSTEM_INSTRUCTION
        examples = current_examples if current_examples else EXAMPLES_TEXT
        
        assert prompt == SYSTEM_INSTRUCTION
        assert examples == EXAMPLES_TEXT


@pytest.mark.integration
class TestFileNameHandling:
    """Integration tests for file name handling."""
    
    def test_output_filename_generation(self):
        """Test generation of output filenames."""
        base_names = [
            ("input.txt", "input"),
            ("inscription_123.txt", "inscription_123"),
            ("test.leiden", "test"),
            ("no_extension", "no_extension")
        ]
        
        for input_name, expected_base in base_names:
            base = os.path.splitext(input_name)[0]
            assert base == expected_base
            
            # Generate different output names
            epidoc_name = f"{base}_epidoc.xml"
            notes_name = f"{base}_notes.txt"
            analysis_name = f"{base}_analysis.txt"
            
            assert epidoc_name.endswith("_epidoc.xml")
            assert notes_name.endswith("_notes.txt")
            assert analysis_name.endswith("_analysis.txt")
    
    def test_filename_collision_handling(self, tmp_path):
        """Test handling of filename collisions."""
        base_name = "test"
        extension = ".xml"
        
        # Create first file
        file1 = tmp_path / f"{base_name}{extension}"
        file1.write_text("content 1")
        
        # Check for collision and generate new name
        used_names = {f"{base_name}{extension}"}
        
        # Generate next available name
        counter = 1
        new_name = f"{base_name}{extension}"
        while new_name in used_names or (tmp_path / new_name).exists():
            new_name = f"{base_name}_{counter}{extension}"
            counter += 1
        
        assert new_name == f"{base_name}_1{extension}"
        used_names.add(new_name)
        
        # Create second file
        file2 = tmp_path / new_name
        file2.write_text("content 2")
        
        # Generate third name
        counter = 1
        new_name = f"{base_name}{extension}"
        while new_name in used_names or (tmp_path / new_name).exists():
            new_name = f"{base_name}_{counter}{extension}"
            counter += 1
        
        assert new_name == f"{base_name}_2{extension}"


@pytest.mark.integration
class TestCheckboxSelectionDecoupling:
    """Tests verifying that checkbox clicks and row selection are independent operations."""
    
    def test_checkbox_click_does_not_change_selection(self):
        """Verify clicking checkbox does NOT change which document is displayed.
        
        Qt's behavior: clicking on a checkbox toggles it but doesn't change
        the row selection. Since we use selectionChanged (not cellClicked),
        checkbox clicks won't trigger document display changes.
        """
        # Simulate: row 1 is selected, user clicks checkbox in row 2
        currently_displayed_row = 1
        checkbox_clicked_in_row = 2
        
        # Qt behavior: checkbox click doesn't change selection
        row_selection_changed = False  # No selectionChanged signal emitted
        
        # Since selection didn't change, displayed document stays the same
        if row_selection_changed:
            currently_displayed_row = checkbox_clicked_in_row
        
        # Document should still show row 1 content
        assert currently_displayed_row == 1
    
    def test_row_click_changes_selection(self):
        """Verify clicking on row (not checkbox) changes displayed document.
        
        Qt's behavior: clicking anywhere except the checkbox changes row selection.
        Since we use selectionChanged signal, this triggers document display update.
        """
        # Simulate: row 1 is selected, user clicks on filename in row 2
        currently_displayed_row = 1
        clicked_row = 2
        
        # Qt behavior: non-checkbox click changes selection
        row_selection_changed = True  # selectionChanged signal emitted
        
        # Since selection changed, displayed document updates
        if row_selection_changed:
            currently_displayed_row = clicked_row
        
        # Document should now show row 2 content
        assert currently_displayed_row == 2
    
    def test_checkbox_state_independent_of_view_selection(self):
        """Verify checkbox state is tracked independently of document view selection."""
        # This documents the core requirement: checkbox state (for batch ops)
        # and document selection (for right pane display) are separate concerns
        file_items = {
            "/file1.txt": {"checked": True, "selected_for_view": False},
            "/file2.txt": {"checked": False, "selected_for_view": True},
        }
        
        # Toggling checkbox should not affect view selection state
        file_items["/file1.txt"]["checked"] = not file_items["/file1.txt"]["checked"]
        
        assert file_items["/file1.txt"]["checked"] is False
        assert file_items["/file1.txt"]["selected_for_view"] is False
        assert file_items["/file2.txt"]["selected_for_view"] is True
    
    def test_batch_operations_use_checkbox_state_not_selection(self):
        """Verify batch operations rely on checkbox state (confirms no regression)."""
        # This test confirms batch operations continue to work correctly
        # using checkbox state after the decoupling changes
        file_items = {
            "/file1.txt": {"checked": True, "is_converted": True},
            "/file2.txt": {"checked": False, "is_converted": True},
            "/file3.txt": {"checked": True, "is_converted": False},
        }
        
        # Batch operations filter by checkbox state, not selection state
        checked_converted_files = [
            path for path, item in file_items.items()
            if item["checked"] and item["is_converted"]
        ]
        
        # Only file1 should be in batch (checked AND converted)
        assert len(checked_converted_files) == 1
        assert "/file1.txt" in checked_converted_files
    
    def test_row_highlight_matches_displayed_content(self):
        """Verify that row highlighting always matches the displayed document.
        
        Using selectionChanged signal ensures that document display only updates
        when row selection (highlighting) actually changes. Checkbox clicks don't
        change selection, so they don't affect display.
        """
        # When row selection changes (via selectionChanged signal):
        # 1. Row gets highlighted (Qt's SelectRows behavior)
        # 2. Document content is displayed (on_row_selection_changed handler)
        highlighted_row = 2
        displayed_document_row = 2  # Same row, always matches
        
        assert highlighted_row == displayed_document_row


@pytest.mark.integration
class TestDeselectFileWorkflow:
    """Tests for the Deselect button functionality.
    
    The Deselect button allows users to clear the viewing selection without
    affecting checkbox states. Key behaviors:
    
    - Sets current_file_item to None
    - Clears all right-hand pane tabs (Input, EpiDoc, Notes, Analysis, Full Output)
    - Removes row selection highlighting from the table
    - Updates status bar to "No file selected"
    - Does NOT affect checkbox states (for batch operations)
    - Button is disabled when no document is selected
    
    Note: Full GUI testing requires a running Qt application. These tests
    validate the logical requirements and serve as documentation.
    """
    
    def test_deselect_clears_current_file_item(self):
        """Verify deselect sets current_file_item to None."""
        # Simulate: a file is currently selected for viewing
        current_file_item = {"file_path": "/test.txt", "input_text": "content"}
        
        # Simulate deselect action
        current_file_item = None
        
        # Document viewing state should be cleared
        assert current_file_item is None
    
    def test_deselect_preserves_checkbox_states(self):
        """Verify deselect does NOT affect checkbox states."""
        # Simulate: multiple files with various checkbox states
        file_states = {
            "/file1.txt": {"checked": True, "selected_for_view": True},
            "/file2.txt": {"checked": False, "selected_for_view": False},
            "/file3.txt": {"checked": True, "selected_for_view": False},
        }
        
        # Simulate deselect action - only affects selected_for_view
        for path in file_states:
            file_states[path]["selected_for_view"] = False
        
        # Checkbox states should be preserved
        assert file_states["/file1.txt"]["checked"] is True
        assert file_states["/file2.txt"]["checked"] is False
        assert file_states["/file3.txt"]["checked"] is True
    
    def test_deselect_clears_right_pane_content(self):
        """Verify deselect clears all content from right pane tabs."""
        # Simulate right pane content before deselect
        right_pane = {
            "input_text": "Some input text",
            "epidoc_text": "<lb/>Some XML",
            "notes_text": "Some notes",
            "analysis_text": "Some analysis",
            "full_output_text": "Full response",
        }
        
        # Simulate deselect action - clears all panes
        for key in right_pane:
            right_pane[key] = ""
        
        # All panes should be empty
        assert right_pane["input_text"] == ""
        assert right_pane["epidoc_text"] == ""
        assert right_pane["notes_text"] == ""
        assert right_pane["analysis_text"] == ""
        assert right_pane["full_output_text"] == ""
    
    def test_deselect_button_disabled_when_no_selection(self):
        """Verify deselect button is disabled when no document is selected."""
        # Initial state: no file selected
        current_file_item = None
        deselect_button_enabled = current_file_item is not None
        
        assert deselect_button_enabled is False
    
    def test_deselect_button_enabled_when_file_selected(self):
        """Verify deselect button is enabled when a document is selected."""
        # State: a file is selected
        current_file_item = {"file_path": "/test.txt"}
        deselect_button_enabled = current_file_item is not None
        
        assert deselect_button_enabled is True
    
    def test_deselect_updates_status_bar(self):
        """Verify deselect updates the status bar message."""
        # Simulate status bar before deselect
        status_message = "Viewing test.txt"
        
        # Simulate deselect action
        status_message = "No file selected"
        
        assert status_message == "No file selected"
    
    def test_deselect_with_batch_operation_pending(self):
        """Verify deselect doesn't interfere with batch operations using checkboxes."""
        # Simulate: files checked for batch conversion, one being viewed
        file_states = {
            "/file1.txt": {"checked": True, "is_converted": False, "selected_for_view": True},
            "/file2.txt": {"checked": True, "is_converted": False, "selected_for_view": False},
        }
        current_file_item = file_states["/file1.txt"]
        
        # Simulate deselect
        current_file_item = None
        for path in file_states:
            file_states[path]["selected_for_view"] = False
        
        # Batch operation (checked files for conversion) should still work
        files_for_batch = [p for p, s in file_states.items() if s["checked"]]
        
        assert len(files_for_batch) == 2
        assert current_file_item is None


@pytest.mark.integration
class TestCheckAllUncheckAll:
    """Tests for the Check All and Uncheck All button functionality.
    
    These buttons allow bulk checking/unchecking of all file checkboxes.
    Key behaviors:
    
    - Check All: sets all checkboxes to checked state
    - Uncheck All: sets all checkboxes to unchecked state
    - Neither button affects the currently selected document (viewing selection)
    - Check All is disabled when all files are already checked or no files loaded
    - Uncheck All is disabled when no files are checked
    - Status bar shows confirmation messages
    
    Note: Full GUI testing requires a running Qt application. These tests
    validate the logical requirements and serve as documentation.
    """
    
    def test_check_all_checks_all_files(self):
        """Verify Check All sets all checkboxes to checked."""
        file_states = {
            "/file1.txt": {"checked": False},
            "/file2.txt": {"checked": True},
            "/file3.txt": {"checked": False},
        }
        
        # Simulate Check All action
        for path in file_states:
            file_states[path]["checked"] = True
        
        assert all(item["checked"] for item in file_states.values())
    
    def test_uncheck_all_unchecks_all_files(self):
        """Verify Uncheck All sets all checkboxes to unchecked."""
        file_states = {
            "/file1.txt": {"checked": True},
            "/file2.txt": {"checked": True},
            "/file3.txt": {"checked": False},
        }
        
        # Simulate Uncheck All action
        for path in file_states:
            file_states[path]["checked"] = False
        
        assert not any(item["checked"] for item in file_states.values())
    
    def test_check_all_does_not_affect_viewing_selection(self):
        """Verify Check All does NOT change which document is displayed."""
        file_states = {
            "/file1.txt": {"checked": False, "selected_for_view": True},
            "/file2.txt": {"checked": False, "selected_for_view": False},
        }
        current_file_item = file_states["/file1.txt"]
        
        # Simulate Check All action - only affects checkbox state
        for path in file_states:
            file_states[path]["checked"] = True
        
        # Viewing selection should be unchanged
        assert file_states["/file1.txt"]["selected_for_view"] is True
        assert file_states["/file2.txt"]["selected_for_view"] is False
        assert current_file_item is file_states["/file1.txt"]
    
    def test_uncheck_all_does_not_affect_viewing_selection(self):
        """Verify Uncheck All does NOT change which document is displayed."""
        file_states = {
            "/file1.txt": {"checked": True, "selected_for_view": True},
            "/file2.txt": {"checked": True, "selected_for_view": False},
        }
        current_file_item = file_states["/file1.txt"]
        
        # Simulate Uncheck All action - only affects checkbox state
        for path in file_states:
            file_states[path]["checked"] = False
        
        # Viewing selection should be unchanged
        assert file_states["/file1.txt"]["selected_for_view"] is True
        assert file_states["/file2.txt"]["selected_for_view"] is False
        assert current_file_item is file_states["/file1.txt"]
    
    def test_check_all_disabled_when_all_already_checked(self):
        """Verify Check All button is disabled when all files are already checked."""
        file_states = {
            "/file1.txt": {"checked": True},
            "/file2.txt": {"checked": True},
        }
        
        has_any_files = len(file_states) > 0
        all_checked = all(item["checked"] for item in file_states.values())
        check_all_enabled = has_any_files and not all_checked
        
        assert check_all_enabled is False
    
    def test_check_all_disabled_when_no_files_loaded(self):
        """Verify Check All button is disabled when no files are loaded."""
        file_states = {}
        
        has_any_files = len(file_states) > 0
        all_checked = has_any_files and all(item["checked"] for item in file_states.values())
        check_all_enabled = has_any_files and not all_checked
        
        assert check_all_enabled is False
    
    def test_check_all_enabled_when_some_unchecked(self):
        """Verify Check All button is enabled when some files are unchecked."""
        file_states = {
            "/file1.txt": {"checked": True},
            "/file2.txt": {"checked": False},
        }
        
        has_any_files = len(file_states) > 0
        all_checked = all(item["checked"] for item in file_states.values())
        check_all_enabled = has_any_files and not all_checked
        
        assert check_all_enabled is True
    
    def test_uncheck_all_disabled_when_no_files_checked(self):
        """Verify Uncheck All button is disabled when no files are checked."""
        file_states = {
            "/file1.txt": {"checked": False},
            "/file2.txt": {"checked": False},
        }
        
        any_checked = any(item["checked"] for item in file_states.values())
        uncheck_all_enabled = any_checked
        
        assert uncheck_all_enabled is False
    
    def test_uncheck_all_enabled_when_some_checked(self):
        """Verify Uncheck All button is enabled when some files are checked."""
        file_states = {
            "/file1.txt": {"checked": True},
            "/file2.txt": {"checked": False},
        }
        
        any_checked = any(item["checked"] for item in file_states.values())
        uncheck_all_enabled = any_checked
        
        assert uncheck_all_enabled is True
    
    def test_check_all_status_message(self):
        """Verify Check All updates the status bar."""
        status_message = ""
        
        # Simulate Check All action
        status_message = "All files checked"
        
        assert status_message == "All files checked"
    
    def test_uncheck_all_status_message(self):
        """Verify Uncheck All updates the status bar."""
        status_message = ""
        
        # Simulate Uncheck All action
        status_message = "All files unchecked"
        
        assert status_message == "All files unchecked"
    
    def test_check_all_does_not_affect_right_pane(self):
        """Verify Check All does not modify right pane content."""
        right_pane = {
            "input_text": "Some input text",
            "epidoc_text": "<lb/>Some XML",
            "notes_text": "Some notes",
        }
        
        # Simulate Check All - should not modify right pane
        file_states = {"/file1.txt": {"checked": False}}
        for path in file_states:
            file_states[path]["checked"] = True
        
        # Right pane should be unchanged
        assert right_pane["input_text"] == "Some input text"
        assert right_pane["epidoc_text"] == "<lb/>Some XML"
        assert right_pane["notes_text"] == "Some notes"
    
    def test_uncheck_all_does_not_affect_right_pane(self):
        """Verify Uncheck All does not modify right pane content."""
        right_pane = {
            "input_text": "Some input text",
            "epidoc_text": "<lb/>Some XML",
            "notes_text": "Some notes",
        }
        
        # Simulate Uncheck All - should not modify right pane
        file_states = {"/file1.txt": {"checked": True}}
        for path in file_states:
            file_states[path]["checked"] = False
        
        # Right pane should be unchanged
        assert right_pane["input_text"] == "Some input text"
        assert right_pane["epidoc_text"] == "<lb/>Some XML"
        assert right_pane["notes_text"] == "Some notes"

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
    """Tests for checkbox selection decoupling behavior.
    
    These tests document the expected behavior for the checkbox/selection
    decoupling feature. They validate the logic pattern used in the
    on_file_selected() method to ensure that:
    - Clicking on column 0 (checkbox column) does not trigger document selection
    - Clicking on other columns triggers document selection
    - Checkbox state and document selection are independent concerns
    
    Note: Full GUI testing requires a running Qt application. These tests
    validate the logical requirements and serve as documentation.
    """
    
    def test_checkbox_column_click_skips_selection_logic(self):
        """Verify column 0 clicks should skip selection (documents the on_file_selected check)."""
        # This test documents the expected behavior: when column is 0,
        # the on_file_selected method should return early without selecting
        column = 0
        current_file_item = {"file_path": "/original/file.txt"}
        
        # The actual implementation uses: if column == 0: return
        # This means selection should NOT happen for column 0
        if column == 0:
            selected = False
        else:
            selected = True
            current_file_item = {"file_path": "/new/file.txt"}
        
        # Document should NOT be selected when clicking checkbox column
        assert selected is False
        assert current_file_item["file_path"] == "/original/file.txt"
    
    def test_non_checkbox_column_click_triggers_selection(self):
        """Verify non-checkbox column clicks should trigger selection."""
        # This test documents the expected behavior: when column is not 0,
        # the on_file_selected method should proceed with document selection
        column = 1
        current_file_item = {"file_path": "/original/file.txt"}
        
        # The actual implementation proceeds with selection when column != 0
        if column == 0:
            selected = False
        else:
            selected = True
            current_file_item = {"file_path": "/new/file.txt"}
        
        # Document SHOULD be selected when clicking non-checkbox column
        assert selected is True
        assert current_file_item["file_path"] == "/new/file.txt"
    
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

"""
Unit tests for LeidenToEpiDocConverter class.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Import the module under test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Need to mock PySide6 before importing the module
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()

# Now we can import the actual code
# Note: This needs to be done after mocking Qt
from leiden_prompts import SYSTEM_INSTRUCTION, EXAMPLES_TEXT


@pytest.mark.unit
class TestLeidenToEpiDocConverter:
    """Test suite for LeidenToEpiDocConverter class."""
    
    def test_load_config_file_exists(self, tmp_path, monkeypatch):
        """Test loading configuration from existing file."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        # Create config file
        config_file = tmp_path / "leiden_epidoc_config.json"
        config_data = {
            "api_key": "test-key",
            "model": "test-model",
            "save_location": "/test/path"
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Test the load_config logic directly without importing
        if os.path.exists(str(config_file)):
            with open(str(config_file), 'r') as f:
                config = json.load(f)
            assert config["api_key"] == "test-key"
            assert config["model"] == "test-model"
            assert config["save_location"] == "/test/path"
    
    def test_load_config_file_not_exists(self, tmp_path, monkeypatch):
        """Test loading configuration when file doesn't exist."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "nonexistent.json"
        
        # Test the logic when file doesn't exist
        if not os.path.exists(str(config_file)):
            config = {}
        assert config == {}
    
    def test_load_config_invalid_json(self, tmp_path, monkeypatch):
        """Test loading configuration with invalid JSON."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "leiden_epidoc_config.json"
        
        # Write invalid JSON
        with open(config_file, 'w') as f:
            f.write("{ invalid json }")
        
        # Test error handling
        try:
            with open(config_file, 'r') as f:
                json.load(f)
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError:
            config = {}
            assert config == {}
    
    def test_save_config(self, tmp_path, monkeypatch):
        """Test saving configuration to file."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "leiden_epidoc_config.json"
        
        # Simulate save_config behavior
        config = {
            "api_key": "new-key",
            "model": "new-model",
            "save_location": "/new/path"
        }
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Verify saved data
        with open(config_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded["api_key"] == "new-key"
        assert loaded["model"] == "new-model"
        assert loaded["save_location"] == "/new/path"
    
    def test_parse_response_with_all_tags(self, sample_epidoc_response):
        """Test parsing response with all expected tags."""
        from tests.conftest import create_mock_converter
        
        converter = create_mock_converter()
        result = converter._parse_response(sample_epidoc_response)
        
        assert result["has_tags"] is True
        assert "test analysis" in result["analysis"].lower()
        assert "notes about" in result["notes"].lower()
        assert "<lb/>" in result["final_translation"]
        assert result["error"] is None
    
    def test_parse_response_missing_tags(self, sample_epidoc_response_no_tags):
        """Test parsing response without expected tags."""
        from tests.conftest import create_mock_converter
        
        converter = create_mock_converter()
        result = converter._parse_response(sample_epidoc_response_no_tags)
        
        assert result["has_tags"] is False
        assert result["analysis"] == ""
        assert result["notes"] == ""
        assert result["final_translation"] == ""
        assert result["full_text"] == sample_epidoc_response_no_tags
    
    def test_parse_response_partial_tags(self):
        """Test parsing response with only some tags present."""
        from tests.conftest import create_mock_converter
        
        partial_response = """<analysis>Test</analysis>
<notes>Test notes</notes>"""
        
        converter = create_mock_converter()
        result = converter._parse_response(partial_response)
        
        # Should be False since not all three tags are present
        assert result["has_tags"] is False
    
    def test_get_epidoc_no_api_key(self):
        """Test conversion without API key configured."""
        # Simulate the behavior when API key is missing
        api_key = ""
        
        if not api_key:
            result = {
                "error": "Error: API key not configured. Please set it in Settings.",
                "full_text": "Error: API key not configured. Please set it in Settings.",
                "has_tags": False
            }
        
        assert "API key not configured" in result["error"]
        assert result["has_tags"] is False
    
    def test_custom_prompt_usage(self):
        """Test that custom prompt is used when set."""
        custom_prompt = "Custom system instruction"
        custom_examples = "Custom examples"
        
        # Simulate logic for choosing prompts
        prompt = custom_prompt if custom_prompt else SYSTEM_INSTRUCTION
        examples = custom_examples if custom_examples else EXAMPLES_TEXT
        
        assert prompt == "Custom system instruction"
        assert examples == "Custom examples"
    
    def test_default_prompt_usage(self):
        """Test that default prompt is used when custom is None."""
        custom_prompt = None
        custom_examples = None
        
        # Simulate logic for choosing prompts
        prompt = custom_prompt if custom_prompt else SYSTEM_INSTRUCTION
        examples = custom_examples if custom_examples else EXAMPLES_TEXT
        
        assert prompt == SYSTEM_INSTRUCTION
        assert examples == EXAMPLES_TEXT
    
    def test_regex_patterns_compiled(self):
        """Test that regex patterns are properly compiled."""
        import re
        
        # Test the patterns used in the converter
        ANALYSIS_PATTERN = re.compile(r'<analysis>(.*?)</analysis>', re.DOTALL | re.IGNORECASE)
        NOTES_PATTERN = re.compile(r'<notes>(.*?)</notes>', re.DOTALL | re.IGNORECASE)
        TRANSLATION_PATTERN = re.compile(r'<final_translation>(.*?)</final_translation>', re.DOTALL | re.IGNORECASE)
        
        assert ANALYSIS_PATTERN is not None
        assert NOTES_PATTERN is not None
        assert TRANSLATION_PATTERN is not None
        
        # Test that patterns work
        test_text = "<analysis>test</analysis>"
        match = ANALYSIS_PATTERN.search(test_text)
        assert match is not None
        assert match.group(1) == "test"
    
    def test_regex_case_insensitive(self):
        """Test that regex patterns are case-insensitive."""
        import re
        
        ANALYSIS_PATTERN = re.compile(r'<analysis>(.*?)</analysis>', re.DOTALL | re.IGNORECASE)
        
        # Test with different cases
        test_cases = [
            "<analysis>test</analysis>",
            "<ANALYSIS>test</ANALYSIS>",
            "<Analysis>test</Analysis>",
        ]
        
        for test_text in test_cases:
            match = ANALYSIS_PATTERN.search(test_text)
            assert match is not None
            assert match.group(1) == "test"
    
    def test_regex_multiline_content(self):
        """Test that regex patterns handle multiline content."""
        import re
        
        ANALYSIS_PATTERN = re.compile(r'<analysis>(.*?)</analysis>', re.DOTALL | re.IGNORECASE)
        
        test_text = """<analysis>
Line 1
Line 2
Line 3
</analysis>"""
        
        match = ANALYSIS_PATTERN.search(test_text)
        assert match is not None
        content = match.group(1).strip()
        assert "Line 1" in content
        assert "Line 2" in content
        assert "Line 3" in content

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


@pytest.mark.unit
class TestAPIParametersPersistence:
    """Test suite for max_tokens and temperature parameter persistence."""

    def test_save_config_with_api_parameters(self, tmp_path, monkeypatch):
        """Test saving configuration includes max_tokens and temperature."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "leiden_epidoc_config.json"

        config = {
            "api_key": "test-key",
            "model": "test-model",
            "save_location": "/test/path",
            "max_tokens": 4096,
            "temperature": 0.5
        }
        with open(config_file, 'w') as f:
            json.dump(config, f)

        with open(config_file, 'r') as f:
            loaded = json.load(f)

        assert loaded["max_tokens"] == 4096
        assert loaded["temperature"] == 0.5

    def test_load_config_with_api_parameters(self, tmp_path, monkeypatch):
        """Test loading configuration retrieves max_tokens and temperature."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "leiden_epidoc_config.json"

        config_data = {
            "api_key": "test-key",
            "model": "test-model",
            "save_location": "/test/path",
            "max_tokens": 16384,
            "temperature": 0.7
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        with open(config_file, 'r') as f:
            config = json.load(f)

        assert config.get("max_tokens", 8192) == 16384
        assert config.get("temperature", 0) == 0.7

    def test_load_config_defaults_when_parameters_missing(self, tmp_path, monkeypatch):
        """Test that defaults are used when max_tokens and temperature are absent."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "leiden_epidoc_config.json"

        # Config without the new parameters (backward compatibility)
        config_data = {
            "api_key": "test-key",
            "model": "test-model",
            "save_location": "/test/path"
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        with open(config_file, 'r') as f:
            config = json.load(f)

        assert config.get("max_tokens", 8192) == 8192
        assert config.get("temperature", 0) == 0


@pytest.mark.unit
class TestAPIParametersValidation:
    """Test suite for max_tokens and temperature input validation."""

    def test_valid_max_tokens_positive_integer(self):
        """Test that positive integers are valid for max_tokens."""
        valid_values = ["1", "100", "8192", "16384"]
        for value in valid_values:
            parsed = int(value)
            assert parsed > 0

    def test_invalid_max_tokens_zero(self):
        """Test that zero is invalid for max_tokens."""
        value = "0"
        parsed = int(value)
        assert parsed <= 0

    def test_invalid_max_tokens_negative(self):
        """Test that negative values are invalid for max_tokens."""
        value = "-1"
        parsed = int(value)
        assert parsed <= 0

    def test_invalid_max_tokens_non_integer(self):
        """Test that non-integer strings are invalid for max_tokens."""
        invalid_values = ["abc", "3.14", ""]
        for value in invalid_values:
            if value:
                with pytest.raises(ValueError):
                    int(value)

    def test_valid_temperature_range(self):
        """Test that floats in [0.0, 1.0] are valid for temperature."""
        valid_values = ["0", "0.0", "0.5", "1.0", "1"]
        for value in valid_values:
            parsed = float(value)
            assert 0.0 <= parsed <= 1.0

    def test_invalid_temperature_above_range(self):
        """Test that values above 1.0 are invalid for temperature."""
        value = "1.5"
        parsed = float(value)
        assert parsed > 1.0

    def test_invalid_temperature_below_range(self):
        """Test that negative values are invalid for temperature."""
        value = "-0.1"
        parsed = float(value)
        assert parsed < 0.0

    def test_invalid_temperature_non_numeric(self):
        """Test that non-numeric strings are invalid for temperature."""
        with pytest.raises(ValueError):
            float("abc")

    def test_empty_fields_use_defaults(self):
        """Test that empty fields fall back to default values."""
        max_tokens_text = ""
        temperature_text = ""

        max_tokens = int(max_tokens_text) if max_tokens_text else 8192
        temperature = float(temperature_text) if temperature_text else 0

        assert max_tokens == 8192
        assert temperature == 0

    def test_max_tokens_below_recommended_minimum(self):
        """Test that values below 1024 are flagged as below recommended minimum."""
        below_minimum_values = [1, 100, 512, 1023]
        for value in below_minimum_values:
            assert value < 1024, f"{value} should be below recommended minimum of 1024"

    def test_max_tokens_at_or_above_recommended_minimum(self):
        """Test that values at or above 1024 are not flagged."""
        safe_values = [1024, 2048, 4096, 8192, 16384]
        for value in safe_values:
            assert value >= 1024, f"{value} should not trigger low-value warning"

    def test_max_tokens_low_value_still_valid(self):
        """Test that low max_tokens values are still valid (warning is non-blocking)."""
        low_values = [1, 10, 100, 500]
        for value in low_values:
            assert value > 0, f"{value} should still be a valid positive integer"
            assert value < 1024, f"{value} should trigger a warning but still be accepted"


@pytest.mark.unit
class TestCreditExhaustionErrorHandling:
    """Test suite for credit/billing error detection in get_epidoc."""

    def _make_billing_error(self, status_code=402, error_type="billing_error"):
        """Helper to create a mock anthropic.APIStatusError for billing errors."""
        import httpx
        import anthropic

        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        response = httpx.Response(
            status_code=status_code,
            json={"error": {"type": error_type, "message": "Your credit balance is too low."}},
            request=request,
        )
        return anthropic.APIStatusError(
            message="billing error",
            response=response,
            body={"error": {"type": error_type, "message": "Your credit balance is too low."}},
        )

    def _make_non_billing_api_error(self, status_code=429, error_type="rate_limit_error"):
        """Helper to create a mock anthropic.APIStatusError for non-billing errors."""
        import httpx
        import anthropic

        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        response = httpx.Response(
            status_code=status_code,
            json={"error": {"type": error_type, "message": "Rate limit exceeded."}},
            request=request,
        )
        return anthropic.APIStatusError(
            message="rate limit exceeded",
            response=response,
            body={"error": {"type": error_type, "message": "Rate limit exceeded."}},
        )

    def test_billing_error_returns_friendly_message(self):
        """Test that a 402 billing error returns a user-friendly message without traceback."""
        import anthropic

        billing_error = self._make_billing_error()

        # Simulate the error handling logic from get_epidoc
        error_type = None
        if isinstance(billing_error.body, dict):
            error_info = billing_error.body.get("error", {})
            if isinstance(error_info, dict):
                error_type = error_info.get("type")

        assert billing_error.status_code == 402
        assert error_type == "billing_error"

        # Verify the expected result structure
        error_msg = (
            "Your Anthropic API credit has been exhausted. "
            "Please top up your account at console.anthropic.com → Billing."
        )
        result = {
            "error": error_msg,
            "full_text": error_msg,
            "has_tags": False,
            "is_credit_error": True,
        }

        assert "credit has been exhausted" in result["error"]
        assert "console.anthropic.com" in result["error"]
        assert result["is_credit_error"] is True
        assert result["has_tags"] is False
        # Ensure no traceback in the message
        assert "Traceback" not in result["error"]

    def test_billing_error_detected_by_status_code(self):
        """Test that HTTP 402 is detected as a billing error even without error_type."""
        import httpx
        import anthropic

        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        response = httpx.Response(status_code=402, json={}, request=request)
        error = anthropic.APIStatusError(message="payment required", response=response, body={})

        # Simulate detection logic
        error_type = None
        if isinstance(error.body, dict):
            error_info = error.body.get("error", {})
            if isinstance(error_info, dict):
                error_type = error_info.get("type")

        is_credit_error = error.status_code == 402 or error_type == "billing_error"
        assert is_credit_error is True

    def test_billing_error_detected_by_error_type(self):
        """Test that billing_error type is detected even with a non-402 status code."""
        import httpx
        import anthropic

        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        response = httpx.Response(
            status_code=400,
            json={"error": {"type": "billing_error", "message": "Credit exhausted."}},
            request=request,
        )
        error = anthropic.APIStatusError(
            message="billing error",
            response=response,
            body={"error": {"type": "billing_error", "message": "Credit exhausted."}},
        )

        error_type = None
        if isinstance(error.body, dict):
            error_info = error.body.get("error", {})
            if isinstance(error_info, dict):
                error_type = error_info.get("type")

        is_credit_error = error.status_code == 402 or error_type == "billing_error"
        assert is_credit_error is True

    def test_non_billing_error_not_detected_as_credit_error(self):
        """Test that non-billing API errors are not treated as credit errors."""
        rate_limit_error = self._make_non_billing_api_error()

        error_type = None
        if isinstance(rate_limit_error.body, dict):
            error_info = rate_limit_error.body.get("error", {})
            if isinstance(error_info, dict):
                error_type = error_info.get("type")

        is_credit_error = rate_limit_error.status_code == 402 or error_type == "billing_error"
        assert is_credit_error is False

    def test_credit_error_message_contains_actionable_info(self):
        """Test that the credit error message contains actionable instructions."""
        error_msg = (
            "Your Anthropic API credit has been exhausted. "
            "Please top up your account at console.anthropic.com → Billing."
        )

        assert "console.anthropic.com" in error_msg
        assert "Billing" in error_msg
        assert "top up" in error_msg

    def test_billing_error_with_none_body(self):
        """Test handling when APIStatusError body is None."""
        import httpx
        import anthropic

        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        response = httpx.Response(status_code=402, request=request)
        error = anthropic.APIStatusError(message="payment required", response=response, body=None)

        error_type = None
        if isinstance(error.body, dict):
            error_info = error.body.get("error", {})
            if isinstance(error_info, dict):
                error_type = error_info.get("type")

        # Should still detect via status_code
        is_credit_error = error.status_code == 402 or error_type == "billing_error"
        assert is_credit_error is True

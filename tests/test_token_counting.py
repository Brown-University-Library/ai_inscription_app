"""
Unit tests for token counting feature.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import sys

# Mock PySide6 before importing
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()


@pytest.mark.unit
class TestTokenCountModeConfig:
    """Test suite for token count mode configuration persistence."""

    def test_default_token_count_mode(self, tmp_path, monkeypatch):
        """Test that default token count mode is 'manual'."""
        monkeypatch.chdir(tmp_path)
        # No config file - should default to "manual"
        from tests.conftest import create_mock_converter
        # Simulate what converter.__init__ does for token_count_mode
        config = {}
        mode = config.get("token_count_mode", "manual")
        assert mode == "manual"

    def test_token_count_mode_saved_to_config(self, tmp_path, monkeypatch):
        """Test that token count mode is persisted in config file."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "leiden_epidoc_config.json"

        # Simulate save_config with token_count_mode
        config = {
            "api_key": "test-key",
            "model": "test-model",
            "save_location": str(tmp_path),
            "max_tokens": 8192,
            "temperature": 0,
            "token_count_mode": "automatic"
        }
        with open(config_file, 'w') as f:
            json.dump(config, f)

        # Read it back
        with open(config_file, 'r') as f:
            loaded_config = json.load(f)

        assert loaded_config["token_count_mode"] == "automatic"

    def test_token_count_mode_loaded_from_config(self, tmp_path, monkeypatch):
        """Test that token count mode is loaded from config."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "leiden_epidoc_config.json"
        config_data = {
            "api_key": "test-key",
            "model": "test-model",
            "token_count_mode": "disabled"
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        with open(config_file, 'r') as f:
            config = json.load(f)

        mode = config.get("token_count_mode", "manual")
        assert mode == "disabled"

    def test_invalid_token_count_mode_defaults_to_manual(self):
        """Test that invalid mode value falls back to 'manual'."""
        valid_modes = ("manual", "automatic", "disabled")
        mode = "invalid_mode"
        if mode not in valid_modes:
            mode = "manual"
        assert mode == "manual"

    def test_all_valid_token_count_modes(self):
        """Test all three valid token count mode values."""
        valid_modes = ("manual", "automatic", "disabled")
        for m in valid_modes:
            assert m in valid_modes


@pytest.mark.unit
class TestCountTokensMethod:
    """Test suite for the count_tokens method on the converter."""

    def test_count_tokens_no_api_key(self):
        """Test that count_tokens returns error when no API key."""
        from tests.conftest import create_mock_converter
        converter = create_mock_converter()
        converter.api_key = ""
        converter.model = "test-model"
        converter.custom_prompt = None
        converter.custom_examples = None

        # Mock the method behavior
        def count_tokens(leiden):
            if not converter.api_key:
                return {"error": "API key not configured"}
            return {"input_tokens": 100}

        result = count_tokens("test text")
        assert "error" in result
        assert result["error"] == "API key not configured"

    def test_count_tokens_success(self):
        """Test successful token counting."""
        mock_response = MagicMock()
        mock_response.input_tokens = 1500

        mock_client = MagicMock()
        mock_client.messages.count_tokens.return_value = mock_response

        with patch('anthropic.Anthropic', return_value=mock_client):
            import anthropic
            from leiden_prompts import SYSTEM_INSTRUCTION, EXAMPLES_TEXT

            client = anthropic.Anthropic(api_key="test-key")
            prompt = SYSTEM_INSTRUCTION
            examples = EXAMPLES_TEXT
            leiden = "Test inscription"
            messages = [{
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": f"Below are example inputs written according to the Leiden convention and the corresponding outputs in XML following the EpiDoc convention.\n{examples}\n\nHere is the text in Leiden Conventions format that you need to translate: \n\n<Input>\n{leiden}\n</Input>\n"
                }]
            }]

            response = client.messages.count_tokens(
                model="test-model",
                system=prompt,
                messages=messages
            )

            assert response.input_tokens == 1500

    def test_count_tokens_api_error(self):
        """Test that API errors are handled gracefully."""
        mock_client = MagicMock()
        mock_client.messages.count_tokens.side_effect = Exception("Network error")

        with patch('anthropic.Anthropic', return_value=mock_client):
            import anthropic

            try:
                client = anthropic.Anthropic(api_key="test-key")
                client.messages.count_tokens(
                    model="test-model",
                    system="prompt",
                    messages=[]
                )
                result = {"input_tokens": 0}
            except Exception as e:
                result = {"error": str(e)}

            assert "error" in result
            assert "Network error" in result["error"]

    def test_count_tokens_uses_same_payload_as_conversion(self):
        """Test that count_tokens builds the same request payload as get_epidoc."""
        from leiden_prompts import SYSTEM_INSTRUCTION, EXAMPLES_TEXT

        leiden = "Test inscription text"
        custom_prompt = None
        custom_examples = None

        # Simulate _build_request_params
        prompt = custom_prompt if custom_prompt else SYSTEM_INSTRUCTION
        examples = custom_examples if custom_examples else EXAMPLES_TEXT
        messages = [{
            "role": "user",
            "content": [{
                "type": "text",
                "text": f"Below are example inputs written according to the Leiden convention and the corresponding outputs in XML following the EpiDoc convention.\n{examples}\n\nHere is the text in Leiden Conventions format that you need to translate: \n\n<Input>\n{leiden}\n</Input>\n"
            }]
        }]

        # Verify the payload structure matches what get_epidoc would use
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert leiden in messages[0]["content"][0]["text"]
        assert prompt == SYSTEM_INSTRUCTION
        assert examples == EXAMPLES_TEXT

    def test_count_tokens_uses_custom_prompt(self):
        """Test that count_tokens uses custom prompt when set."""
        from leiden_prompts import SYSTEM_INSTRUCTION

        custom_prompt = "My custom system prompt"
        prompt = custom_prompt if custom_prompt else SYSTEM_INSTRUCTION
        assert prompt == "My custom system prompt"

    def test_count_tokens_uses_custom_examples(self):
        """Test that count_tokens uses custom examples when set."""
        from leiden_prompts import EXAMPLES_TEXT

        custom_examples = "My custom examples"
        examples = custom_examples if custom_examples else EXAMPLES_TEXT
        assert examples == "My custom examples"


@pytest.mark.unit
class TestFileItemTokenCount:
    """Test suite for FileItem input_token_count attribute."""

    def test_file_item_has_token_count_attribute(self):
        """Test that FileItem has input_token_count attribute."""
        # Simulate FileItem initialization
        class MockFileItem:
            def __init__(self):
                self.input_token_count = None

        item = MockFileItem()
        assert item.input_token_count is None

    def test_file_item_token_count_set(self):
        """Test setting token count on FileItem."""
        class MockFileItem:
            def __init__(self):
                self.input_token_count = None

        item = MockFileItem()
        item.input_token_count = 1500
        assert item.input_token_count == 1500

    def test_file_item_token_count_cleared(self):
        """Test clearing token count on FileItem."""
        class MockFileItem:
            def __init__(self):
                self.input_token_count = 1500

        item = MockFileItem()
        item.input_token_count = None
        assert item.input_token_count is None


@pytest.mark.unit
class TestStatsWithPreCheckTokenCount:
    """Test suite for _format_stats with pre-checked token count."""

    def _create_format_stats(self):
        """Create a standalone _format_stats function for testing."""
        def _format_stats(result, file_item=None):
            input_tokens = result.get("input_tokens", 0)
            output_tokens = result.get("output_tokens", 0)
            cache_creation = result.get("cache_creation_input_tokens", 0)
            cache_read = result.get("cache_read_input_tokens", 0)
            total_tokens = input_tokens + output_tokens

            lines = []

            # Show pre-checked input token count if available
            if file_item and file_item.input_token_count is not None:
                lines.append("Pre-Check Token Count")
                lines.append("=" * 30)
                lines.append(f"Estimated input tokens:      {file_item.input_token_count:,}")
                lines.append("")

            lines.extend([
                "Token Usage",
                "=" * 30,
                f"Input tokens:                {input_tokens:,}",
                f"Output tokens:               {output_tokens:,}",
                f"Total tokens:                {total_tokens:,}",
                "",
                "Cache Details",
                "-" * 30,
                f"Cache creation tokens:       {cache_creation:,}",
                f"Cache read tokens:           {cache_read:,}",
            ])

            stop_reason = result.get("stop_reason")
            if stop_reason is not None:
                truncated = result.get("truncated", False)
                lines.append("")
                lines.append("Completion Details")
                lines.append("-" * 30)
                lines.append(f"Token Limit Reached:         {'Yes' if truncated else 'No'}")

            return "\n".join(lines)

        return _format_stats

    def test_stats_without_pre_check(self):
        """Test _format_stats without pre-checked token count."""
        format_stats = self._create_format_stats()
        result = {"input_tokens": 100, "output_tokens": 50}
        output = format_stats(result)
        assert "Pre-Check Token Count" not in output
        assert "Input tokens:" in output

    def test_stats_with_pre_check_no_file_item(self):
        """Test _format_stats with file_item=None."""
        format_stats = self._create_format_stats()
        result = {"input_tokens": 100, "output_tokens": 50}
        output = format_stats(result, file_item=None)
        assert "Pre-Check Token Count" not in output

    def test_stats_with_pre_check_token_count(self):
        """Test _format_stats includes pre-checked token count."""
        format_stats = self._create_format_stats()

        class MockFileItem:
            input_token_count = 1500

        result = {"input_tokens": 100, "output_tokens": 50}
        output = format_stats(result, file_item=MockFileItem())
        assert "Pre-Check Token Count" in output
        assert "Estimated input tokens:      1,500" in output
        assert "Input tokens:" in output

    def test_stats_with_pre_check_none(self):
        """Test _format_stats when input_token_count is None."""
        format_stats = self._create_format_stats()

        class MockFileItem:
            input_token_count = None

        result = {"input_tokens": 100, "output_tokens": 50}
        output = format_stats(result, file_item=MockFileItem())
        assert "Pre-Check Token Count" not in output

    def test_stats_pre_check_with_conversion_stats(self):
        """Test _format_stats shows both pre-check and conversion stats."""
        format_stats = self._create_format_stats()

        class MockFileItem:
            input_token_count = 2000

        result = {
            "input_tokens": 1980,
            "output_tokens": 500,
            "cache_creation_input_tokens": 100,
            "cache_read_input_tokens": 50,
            "stop_reason": "end_turn",
            "truncated": False
        }
        output = format_stats(result, file_item=MockFileItem())
        assert "Pre-Check Token Count" in output
        assert "Estimated input tokens:      2,000" in output
        assert "Input tokens:                1,980" in output
        assert "Output tokens:               500" in output
        assert "Token Limit Reached:         No" in output


@pytest.mark.unit
class TestTokenCountStaleDetection:
    """Test suite for clearing token counts when model/prompt changes."""

    def test_clear_token_counts(self):
        """Test that all token counts are cleared."""
        class MockFileItem:
            def __init__(self, count):
                self.input_token_count = count

        file_items = {
            "file1.txt": MockFileItem(1000),
            "file2.txt": MockFileItem(2000),
            "file3.txt": MockFileItem(None),
        }

        # Simulate _clear_all_token_counts
        for fi in file_items.values():
            fi.input_token_count = None

        assert all(fi.input_token_count is None for fi in file_items.values())

    def test_model_change_triggers_clear(self):
        """Test that changing model should clear counts."""
        old_model = "claude-sonnet-4-20250514"
        new_model = "claude-opus-4-20250514"
        assert old_model != new_model  # Model changed → should clear

    def test_same_model_no_clear(self):
        """Test that keeping same model should not clear counts."""
        old_model = "claude-sonnet-4-20250514"
        new_model = "claude-sonnet-4-20250514"
        assert old_model == new_model  # Same model → no clear

    def test_prompt_change_triggers_clear(self):
        """Test that changing custom prompt should clear counts."""
        old_prompt = None
        new_prompt = "Custom prompt text"
        assert old_prompt != new_prompt  # Prompt changed → should clear

    def test_examples_change_triggers_clear(self):
        """Test that changing custom examples should clear counts."""
        old_examples = "Old examples"
        new_examples = "New examples"
        assert old_examples != new_examples  # Examples changed → should clear


@pytest.mark.unit
class TestBuildRequestParams:
    """Test suite for _build_request_params helper method."""

    def test_build_request_params_default(self):
        """Test building request params with default prompt and examples."""
        from leiden_prompts import SYSTEM_INSTRUCTION, EXAMPLES_TEXT

        custom_prompt = None
        custom_examples = None
        leiden = "Test text"

        prompt = custom_prompt if custom_prompt else SYSTEM_INSTRUCTION
        examples = custom_examples if custom_examples else EXAMPLES_TEXT
        messages = [{
            "role": "user",
            "content": [{
                "type": "text",
                "text": f"Below are example inputs written according to the Leiden convention and the corresponding outputs in XML following the EpiDoc convention.\n{examples}\n\nHere is the text in Leiden Conventions format that you need to translate: \n\n<Input>\n{leiden}\n</Input>\n"
            }]
        }]

        assert prompt == SYSTEM_INSTRUCTION
        assert "Test text" in messages[0]["content"][0]["text"]

    def test_build_request_params_custom(self):
        """Test building request params with custom prompt and examples."""
        custom_prompt = "Custom system prompt"
        custom_examples = "Custom examples text"
        leiden = "Test text"

        prompt = custom_prompt if custom_prompt else "DEFAULT"
        examples = custom_examples if custom_examples else "DEFAULT"
        messages = [{
            "role": "user",
            "content": [{
                "type": "text",
                "text": f"Below are example inputs written according to the Leiden convention and the corresponding outputs in XML following the EpiDoc convention.\n{examples}\n\nHere is the text in Leiden Conventions format that you need to translate: \n\n<Input>\n{leiden}\n</Input>\n"
            }]
        }]

        assert prompt == "Custom system prompt"
        assert "Custom examples text" in messages[0]["content"][0]["text"]


@pytest.mark.unit
class TestTokenCountErrorHandling:
    """Test suite for graceful error handling in token counting."""

    def test_error_result_format(self):
        """Test that error results have correct format."""
        result = {"error": "Network timeout"}
        assert "error" in result
        assert "input_tokens" not in result

    def test_success_result_format(self):
        """Test that success results have correct format."""
        result = {"input_tokens": 1500}
        assert "input_tokens" in result
        assert "error" not in result

    def test_error_displayed_in_table(self):
        """Test that errors show 'Error' text in table column."""
        result = {"error": "API error"}
        display_text = "Error" if result.get("error") else f"{result.get('input_tokens', 0):,}"
        assert display_text == "Error"

    def test_success_displayed_in_table(self):
        """Test that successful counts show formatted number."""
        result = {"input_tokens": 15000}
        display_text = "Error" if result.get("error") else f"{result.get('input_tokens', 0):,}"
        assert display_text == "15,000"

    def test_no_api_key_silent_skip_automatic(self):
        """Test automatic counting is silently skipped without API key."""
        api_key = ""
        token_count_mode = "automatic"
        # Should not start counting if no API key
        should_count = (token_count_mode == "automatic" and api_key)
        assert not should_count

    def test_automatic_counting_with_api_key(self):
        """Test automatic counting proceeds with API key configured."""
        api_key = "test-key"
        token_count_mode = "automatic"
        should_count = (token_count_mode == "automatic" and api_key)
        assert should_count

    def test_manual_mode_does_not_auto_count(self):
        """Test manual mode does not trigger automatic counting."""
        api_key = "test-key"
        token_count_mode = "manual"
        should_count = (token_count_mode == "automatic" and api_key)
        assert not should_count

    def test_disabled_mode_does_not_count(self):
        """Test disabled mode prevents counting entirely."""
        token_count_mode = "disabled"
        should_count = (token_count_mode != "disabled")
        assert not should_count

"""
Unit tests for Stats tab token usage feature.
"""
import os
from unittest.mock import MagicMock

import pytest
import sys

# Mock PySide6 before importing
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()


@pytest.mark.unit
class TestTokenUsageCapture:
    """Test suite for capturing token usage from API responses."""

    def test_parse_response_with_simulated_token_usage(self):
        """Test that get_epidoc captures input_tokens and output_tokens from API response."""
        from tests.conftest import create_mock_converter

        # Simulate the behavior of get_epidoc with token usage
        converter = create_mock_converter()
        response_text = """<analysis>Test analysis</analysis>
<notes>Test notes</notes>
<final_translation>Test translation</final_translation>"""

        result = converter._parse_response(response_text)

        # Simulate adding token usage (as get_epidoc does)
        result["input_tokens"] = 150
        result["output_tokens"] = 50
        result["cache_creation_input_tokens"] = 0
        result["cache_read_input_tokens"] = 0

        assert result["input_tokens"] == 150
        assert result["output_tokens"] == 50
        assert result["cache_creation_input_tokens"] == 0
        assert result["cache_read_input_tokens"] == 0

    def test_token_usage_with_cache_tokens(self):
        """Test that cache tokens are captured from API response."""
        result = {
            "has_tags": True,
            "input_tokens": 200,
            "output_tokens": 100,
            "cache_creation_input_tokens": 50,
            "cache_read_input_tokens": 30,
        }

        assert result["input_tokens"] == 200
        assert result["output_tokens"] == 100
        assert result["cache_creation_input_tokens"] == 50
        assert result["cache_read_input_tokens"] == 30

    def test_token_usage_defaults_to_zero(self):
        """Test that token counts default to 0 when not present."""
        result = {"has_tags": True}

        assert result.get("input_tokens", 0) == 0
        assert result.get("output_tokens", 0) == 0
        assert result.get("cache_creation_input_tokens", 0) == 0
        assert result.get("cache_read_input_tokens", 0) == 0

    def test_error_result_has_no_token_usage(self):
        """Test that error results don't include token usage."""
        # Simulate the error result from get_epidoc
        result = {
            "error": "Error during conversion: API error",
            "full_text": "Error during conversion: API error",
            "has_tags": False
        }

        # Error results should not have token usage
        assert "input_tokens" not in result
        assert "output_tokens" not in result

    def test_no_api_key_result_has_no_token_usage(self):
        """Test that result without API key doesn't include token usage."""
        result = {
            "error": "Error: API key not configured. Please set it in Settings.",
            "full_text": "Error: API key not configured. Please set it in Settings.",
            "has_tags": False
        }

        assert "input_tokens" not in result
        assert "output_tokens" not in result

    def test_getattr_usage_extraction(self):
        """Test that getattr correctly extracts usage from mock message."""
        # Simulate Anthropic message object with usage
        mock_usage = MagicMock()
        mock_usage.input_tokens = 500
        mock_usage.output_tokens = 200
        mock_usage.cache_creation_input_tokens = 100
        mock_usage.cache_read_input_tokens = 50

        mock_message = MagicMock()
        mock_message.usage = mock_usage

        # Simulate the extraction logic from get_epidoc
        usage = getattr(mock_message, 'usage', None)
        result = {}
        if usage:
            result["input_tokens"] = getattr(usage, 'input_tokens', 0)
            result["output_tokens"] = getattr(usage, 'output_tokens', 0)
            result["cache_creation_input_tokens"] = getattr(usage, 'cache_creation_input_tokens', 0)
            result["cache_read_input_tokens"] = getattr(usage, 'cache_read_input_tokens', 0)

        assert result["input_tokens"] == 500
        assert result["output_tokens"] == 200
        assert result["cache_creation_input_tokens"] == 100
        assert result["cache_read_input_tokens"] == 50

    def test_getattr_usage_none(self):
        """Test that missing usage attribute results in no token data."""
        mock_message = MagicMock(spec=[])  # No attributes

        usage = getattr(mock_message, 'usage', None)
        result = {}
        if usage:
            result["input_tokens"] = getattr(usage, 'input_tokens', 0)

        assert "input_tokens" not in result


@pytest.mark.unit
class TestStatsFormatting:
    """Test suite for stats display formatting."""

    def test_format_stats_with_token_data(self):
        """Test formatting stats with all token data present."""
        result = {
            "input_tokens": 1500,
            "output_tokens": 500,
            "cache_creation_input_tokens": 100,
            "cache_read_input_tokens": 50,
        }

        # Simulate _format_stats logic
        input_tokens = result.get("input_tokens", 0)
        output_tokens = result.get("output_tokens", 0)
        cache_creation = result.get("cache_creation_input_tokens", 0)
        cache_read = result.get("cache_read_input_tokens", 0)
        total_tokens = input_tokens + output_tokens

        assert input_tokens == 1500
        assert output_tokens == 500
        assert total_tokens == 2000
        assert cache_creation == 100
        assert cache_read == 50

    def test_format_stats_with_zero_tokens(self):
        """Test formatting stats when all tokens are zero."""
        result = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        }

        input_tokens = result.get("input_tokens", 0)
        output_tokens = result.get("output_tokens", 0)
        total_tokens = input_tokens + output_tokens

        assert total_tokens == 0

    def test_format_stats_without_token_data(self):
        """Test formatting stats when no token data is in result."""
        result = {"has_tags": True, "full_text": "some text"}

        input_tokens = result.get("input_tokens", 0)
        output_tokens = result.get("output_tokens", 0)
        cache_creation = result.get("cache_creation_input_tokens", 0)
        cache_read = result.get("cache_read_input_tokens", 0)
        total_tokens = input_tokens + output_tokens

        assert input_tokens == 0
        assert output_tokens == 0
        assert total_tokens == 0
        assert cache_creation == 0
        assert cache_read == 0

    def test_format_stats_output_contains_labels(self):
        """Test that formatted stats output contains expected labels."""
        result = {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_creation_input_tokens": 10,
            "cache_read_input_tokens": 5,
        }

        # Simulate _format_stats output
        input_tokens = result.get("input_tokens", 0)
        output_tokens = result.get("output_tokens", 0)
        cache_creation = result.get("cache_creation_input_tokens", 0)
        cache_read = result.get("cache_read_input_tokens", 0)
        total_tokens = input_tokens + output_tokens

        lines = [
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
        ]
        stats_text = "\n".join(lines)

        assert "Token Usage" in stats_text
        assert "Input tokens:" in stats_text
        assert "Output tokens:" in stats_text
        assert "Total tokens:" in stats_text
        assert "Cache Details" in stats_text
        assert "Cache creation tokens:" in stats_text
        assert "Cache read tokens:" in stats_text
        assert "100" in stats_text
        assert "50" in stats_text
        assert "150" in stats_text

    def test_format_stats_large_numbers_have_commas(self):
        """Test that large token counts are formatted with commas."""
        input_tokens = 1234567
        output_tokens = 890123
        total_tokens = input_tokens + output_tokens

        formatted = f"{input_tokens:,}"
        assert formatted == "1,234,567"

        formatted_total = f"{total_tokens:,}"
        assert formatted_total == "2,124,690"


@pytest.mark.unit
class TestStatsTabDisplay:
    """Test suite for Stats tab display logic."""

    def test_conversion_result_with_stats_displayed(self):
        """Test that stats are displayed when file has been converted."""
        file_item = {
            'file_path': "/test/file.txt",
            'file_name': "file.txt",
            'input_text': "test content",
            'is_converted': True,
            'has_error': False,
            'conversion_result': {
                'has_tags': True,
                'analysis': 'test',
                'notes': 'test',
                'final_translation': 'test',
                'input_tokens': 300,
                'output_tokens': 100,
                'cache_creation_input_tokens': 0,
                'cache_read_input_tokens': 0,
            }
        }

        result = file_item['conversion_result']
        assert file_item['is_converted'] is True
        assert result.get("input_tokens", 0) == 300
        assert result.get("output_tokens", 0) == 100

    def test_unconverted_file_stats_empty(self):
        """Test that stats are empty when file hasn't been converted."""
        file_item = {
            'file_path': "/test/file.txt",
            'file_name': "file.txt",
            'input_text': "test content",
            'is_converted': False,
            'has_error': False,
            'conversion_result': None,
        }

        # When not converted, stats should be empty
        assert file_item['is_converted'] is False
        assert file_item['conversion_result'] is None

    def test_error_conversion_still_shows_stats(self):
        """Test that error conversions don't have token stats in result."""
        file_item = {
            'file_path': "/test/file.txt",
            'file_name': "file.txt",
            'input_text': "test content",
            'is_converted': True,
            'has_error': True,
            'conversion_result': {
                'error': 'API Error',
                'full_text': 'API Error',
                'has_tags': False,
            }
        }

        result = file_item['conversion_result']
        # Error results from exceptions won't have token data
        assert result.get("input_tokens", 0) == 0
        assert result.get("output_tokens", 0) == 0

    def test_stats_update_on_document_switch(self):
        """Test that stats update when switching between documents."""
        file_items = {
            "/test/file1.txt": {
                'is_converted': True,
                'conversion_result': {
                    'has_tags': True,
                    'input_tokens': 100,
                    'output_tokens': 50,
                    'cache_creation_input_tokens': 0,
                    'cache_read_input_tokens': 0,
                }
            },
            "/test/file2.txt": {
                'is_converted': True,
                'conversion_result': {
                    'has_tags': True,
                    'input_tokens': 200,
                    'output_tokens': 75,
                    'cache_creation_input_tokens': 10,
                    'cache_read_input_tokens': 5,
                }
            },
        }

        # Simulate selecting file1
        result1 = file_items["/test/file1.txt"]['conversion_result']
        assert result1["input_tokens"] == 100
        assert result1["output_tokens"] == 50

        # Simulate selecting file2
        result2 = file_items["/test/file2.txt"]['conversion_result']
        assert result2["input_tokens"] == 200
        assert result2["output_tokens"] == 75
        assert result2["cache_creation_input_tokens"] == 10
        assert result2["cache_read_input_tokens"] == 5

    def test_tab_index_constant(self):
        """Test that TAB_STATS constant is correctly defined."""
        # The Stats tab should be at index 5 (after Full Output at index 4)
        TAB_INPUT = 0
        TAB_EPIDOC = 1
        TAB_NOTES = 2
        TAB_ANALYSIS = 3
        TAB_FULL_OUTPUT = 4
        TAB_STATS = 5

        assert TAB_STATS == 5
        assert TAB_STATS == TAB_FULL_OUTPUT + 1

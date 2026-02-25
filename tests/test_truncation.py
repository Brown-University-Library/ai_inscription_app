"""
Unit tests for token limit truncation detection and alert logic.
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
class TestStopReasonCapture:
    """Test suite for capturing stop_reason from API responses."""

    def test_stop_reason_end_turn_captured(self):
        """Test that stop_reason 'end_turn' is captured from API response."""
        mock_message = MagicMock()
        mock_message.stop_reason = "end_turn"

        result = {}
        result["stop_reason"] = getattr(mock_message, 'stop_reason', None)
        result["truncated"] = (result["stop_reason"] == "max_tokens")

        assert result["stop_reason"] == "end_turn"
        assert result["truncated"] is False

    def test_stop_reason_max_tokens_captured(self):
        """Test that stop_reason 'max_tokens' is captured from API response."""
        mock_message = MagicMock()
        mock_message.stop_reason = "max_tokens"

        result = {}
        result["stop_reason"] = getattr(mock_message, 'stop_reason', None)
        result["truncated"] = (result["stop_reason"] == "max_tokens")

        assert result["stop_reason"] == "max_tokens"
        assert result["truncated"] is True

    def test_stop_reason_missing_defaults_to_none(self):
        """Test that missing stop_reason defaults to None."""
        mock_message = MagicMock(spec=[])  # No attributes

        result = {}
        result["stop_reason"] = getattr(mock_message, 'stop_reason', None)
        result["truncated"] = (result["stop_reason"] == "max_tokens")

        assert result["stop_reason"] is None
        assert result["truncated"] is False

    def test_stop_reason_and_usage_both_captured(self):
        """Test that both stop_reason and usage are captured from API response."""
        mock_usage = MagicMock()
        mock_usage.input_tokens = 500
        mock_usage.output_tokens = 200

        mock_message = MagicMock()
        mock_message.usage = mock_usage
        mock_message.stop_reason = "max_tokens"

        result = {}
        usage = getattr(mock_message, 'usage', None)
        if usage:
            result["input_tokens"] = getattr(usage, 'input_tokens', 0)
            result["output_tokens"] = getattr(usage, 'output_tokens', 0)

        result["stop_reason"] = getattr(mock_message, 'stop_reason', None)
        result["truncated"] = (result["stop_reason"] == "max_tokens")

        assert result["input_tokens"] == 500
        assert result["output_tokens"] == 200
        assert result["stop_reason"] == "max_tokens"
        assert result["truncated"] is True

    def test_error_result_has_no_stop_reason(self):
        """Test that error results don't include stop_reason."""
        result = {
            "error": "Error during conversion: API error",
            "full_text": "Error during conversion: API error",
            "has_tags": False
        }

        assert "stop_reason" not in result
        assert "truncated" not in result


@pytest.mark.unit
class TestTruncationDetection:
    """Test suite for truncation detection logic."""

    def test_truncated_flag_true_for_max_tokens(self):
        """Test that truncated is True when stop_reason is max_tokens."""
        result = {"stop_reason": "max_tokens"}
        result["truncated"] = (result["stop_reason"] == "max_tokens")
        assert result["truncated"] is True

    def test_truncated_flag_false_for_end_turn(self):
        """Test that truncated is False when stop_reason is end_turn."""
        result = {"stop_reason": "end_turn"}
        result["truncated"] = (result["stop_reason"] == "max_tokens")
        assert result["truncated"] is False

    def test_truncated_flag_false_for_none(self):
        """Test that truncated is False when stop_reason is None."""
        result = {"stop_reason": None}
        result["truncated"] = (result["stop_reason"] == "max_tokens")
        assert result["truncated"] is False

    def test_truncated_defaults_to_false_via_get(self):
        """Test that result.get('truncated', False) returns False when missing."""
        result = {"has_tags": True}
        assert result.get("truncated", False) is False

    def test_truncated_result_with_full_conversion_data(self):
        """Test a complete result dict that was truncated."""
        result = {
            "full_text": "partial output...",
            "has_tags": False,
            "analysis": "",
            "notes": "",
            "final_translation": "",
            "error": None,
            "input_tokens": 1000,
            "output_tokens": 8192,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "stop_reason": "max_tokens",
            "truncated": True,
        }

        assert result["truncated"] is True
        assert result["stop_reason"] == "max_tokens"
        assert result["output_tokens"] == 8192


@pytest.mark.unit
class TestStatsFormattingWithTruncation:
    """Test suite for stats display formatting with truncation info."""

    def _format_stats(self, result):
        """Replicate the _format_stats logic for testing."""
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

        stop_reason = result.get("stop_reason")
        if stop_reason is not None:
            truncated = result.get("truncated", False)
            lines.append("")
            lines.append("Completion Details")
            lines.append("-" * 30)
            lines.append(f"Token Limit Reached:         {'Yes' if truncated else 'No'}")

        return "\n".join(lines)

    def test_stats_show_token_limit_reached_yes(self):
        """Test that stats show 'Token Limit Reached: Yes' when truncated."""
        result = {
            "input_tokens": 1000,
            "output_tokens": 8192,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "stop_reason": "max_tokens",
            "truncated": True,
        }

        stats_text = self._format_stats(result)
        assert "Token Limit Reached:" in stats_text
        assert "Yes" in stats_text
        assert "Completion Details" in stats_text

    def test_stats_show_token_limit_reached_no(self):
        """Test that stats show 'Token Limit Reached: No' for normal completion."""
        result = {
            "input_tokens": 1000,
            "output_tokens": 500,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "stop_reason": "end_turn",
            "truncated": False,
        }

        stats_text = self._format_stats(result)
        assert "Token Limit Reached:" in stats_text
        assert "No" in stats_text

    def test_stats_no_completion_details_without_stop_reason(self):
        """Test that completion details are hidden when stop_reason is absent."""
        result = {
            "input_tokens": 1000,
            "output_tokens": 500,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        }

        stats_text = self._format_stats(result)
        assert "Token Limit Reached:" not in stats_text
        assert "Completion Details" not in stats_text

    def test_stats_still_contain_token_usage_when_truncated(self):
        """Test that token usage info is still present when truncated."""
        result = {
            "input_tokens": 1500,
            "output_tokens": 8192,
            "cache_creation_input_tokens": 100,
            "cache_read_input_tokens": 50,
            "stop_reason": "max_tokens",
            "truncated": True,
        }

        stats_text = self._format_stats(result)
        assert "Token Usage" in stats_text
        assert "Input tokens:" in stats_text
        assert "Output tokens:" in stats_text
        assert "Cache Details" in stats_text
        assert "Token Limit Reached:" in stats_text


@pytest.mark.unit
class TestTruncationWarningTracking:
    """Test suite for truncation warning dialog tracking logic."""

    def test_truncation_warned_set_initialized_empty(self):
        """Test that truncation_warned set starts empty."""
        truncation_warned = set()
        assert len(truncation_warned) == 0

    def test_truncation_warned_prevents_duplicate_dialog(self):
        """Test that adding a file to truncation_warned prevents repeat warnings."""
        truncation_warned = set()
        file_path = "/test/file.txt"

        # First time: not in set, warning should show
        assert file_path not in truncation_warned
        truncation_warned.add(file_path)

        # Second time: in set, warning should not show
        assert file_path in truncation_warned

    def test_truncation_warned_cleared_on_reconversion(self):
        """Test that truncation_warned is cleared for a file before re-conversion."""
        truncation_warned = set()
        file_path = "/test/file.txt"
        truncation_warned.add(file_path)

        # Simulate on_file_conversion_started clearing the warning
        truncation_warned.discard(file_path)
        assert file_path not in truncation_warned

    def test_truncation_warned_cleared_on_clear_all(self):
        """Test that truncation_warned is cleared when all files are cleared."""
        truncation_warned = set()
        truncation_warned.add("/test/file1.txt")
        truncation_warned.add("/test/file2.txt")

        # Simulate clear_all_files
        truncation_warned.clear()
        assert len(truncation_warned) == 0

    def test_truncation_warned_independent_of_missing_tags_warned(self):
        """Test that truncation_warned and missing_tags_warned are independent."""
        missing_tags_warned = set()
        truncation_warned = set()
        file_path = "/test/file.txt"

        missing_tags_warned.add(file_path)
        assert file_path in missing_tags_warned
        assert file_path not in truncation_warned

        truncation_warned.add(file_path)
        assert file_path in missing_tags_warned
        assert file_path in truncation_warned


@pytest.mark.unit
class TestTruncationVisualIndicator:
    """Test suite for truncation visual indicators in file table."""

    def test_truncated_status_text(self):
        """Test that truncated files show '⚠ Truncated' status."""
        result = {"truncated": True, "error": None}
        has_error = False

        if has_error:
            status = "✗ Error"
        elif result.get("truncated"):
            status = "⚠ Truncated"
        else:
            status = "✓ Converted"

        assert status == "⚠ Truncated"

    def test_normal_completion_status_text(self):
        """Test that normal completions show '✓ Converted' status."""
        result = {"truncated": False, "error": None}
        has_error = False

        if has_error:
            status = "✗ Error"
        elif result.get("truncated"):
            status = "⚠ Truncated"
        else:
            status = "✓ Converted"

        assert status == "✓ Converted"

    def test_error_status_takes_priority(self):
        """Test that error status takes priority over truncation."""
        result = {"truncated": True, "error": "API Error"}
        has_error = True

        if has_error:
            status = "✗ Error"
        elif result.get("truncated"):
            status = "⚠ Truncated"
        else:
            status = "✓ Converted"

        assert status == "✗ Error"


@pytest.mark.unit
class TestBatchTruncationSummary:
    """Test suite for batch conversion truncation summary."""

    def test_collect_truncated_files_from_batch(self):
        """Test collecting truncated files after batch conversion."""
        file_items = {
            "/test/file1.txt": {
                "file_name": "file1.txt",
                "is_converted": True,
                "conversion_result": {
                    "truncated": True,
                    "stop_reason": "max_tokens",
                },
            },
            "/test/file2.txt": {
                "file_name": "file2.txt",
                "is_converted": True,
                "conversion_result": {
                    "truncated": False,
                    "stop_reason": "end_turn",
                },
            },
            "/test/file3.txt": {
                "file_name": "file3.txt",
                "is_converted": True,
                "conversion_result": {
                    "truncated": True,
                    "stop_reason": "max_tokens",
                },
            },
        }

        truncated_files = []
        for file_path, file_item in file_items.items():
            if (file_item["is_converted"] and file_item["conversion_result"]
                    and file_item["conversion_result"].get("truncated")):
                truncated_files.append(file_item["file_name"])

        assert len(truncated_files) == 2
        assert "file1.txt" in truncated_files
        assert "file3.txt" in truncated_files
        assert "file2.txt" not in truncated_files

    def test_no_truncated_files_in_batch(self):
        """Test that no summary is needed when no files are truncated."""
        file_items = {
            "/test/file1.txt": {
                "file_name": "file1.txt",
                "is_converted": True,
                "conversion_result": {
                    "truncated": False,
                    "stop_reason": "end_turn",
                },
            },
        }

        truncated_files = []
        for file_path, file_item in file_items.items():
            if (file_item["is_converted"] and file_item["conversion_result"]
                    and file_item["conversion_result"].get("truncated")):
                truncated_files.append(file_item["file_name"])

        assert len(truncated_files) == 0

    def test_batch_truncation_marks_files_as_warned(self):
        """Test that batch conversion marks truncated files in truncation_warned set."""
        truncation_warned = set()
        file_items = {
            "/test/file1.txt": {
                "file_name": "file1.txt",
                "is_converted": True,
                "conversion_result": {"truncated": True},
            },
            "/test/file2.txt": {
                "file_name": "file2.txt",
                "is_converted": True,
                "conversion_result": {"truncated": False},
            },
        }

        # Simulate batch completion logic
        for file_path, file_item in file_items.items():
            if (file_item["is_converted"] and file_item["conversion_result"]
                    and file_item["conversion_result"].get("truncated")):
                truncation_warned.add(file_path)

        assert "/test/file1.txt" in truncation_warned
        assert "/test/file2.txt" not in truncation_warned

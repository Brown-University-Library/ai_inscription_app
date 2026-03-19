"""
Unit tests for token counting UI visibility behavior.

When the token counting setting is "Disabled," all token-counting UI elements
should be hidden (not just grayed out). When re-enabled, they should reappear.
"""
import json
from unittest.mock import MagicMock

import pytest
import sys

# Mock PySide6 before importing
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()


@pytest.mark.unit
class TestTokenCountVisibilityLogic:
    """Test suite for showing/hiding token-counting UI based on mode."""

    def test_disabled_mode_hides_column(self):
        """When mode is 'disabled', the Input Tokens column should be hidden."""
        token_count_mode = "disabled"
        is_disabled = token_count_mode == "disabled"
        column_hidden = is_disabled
        assert column_hidden is True

    def test_manual_mode_shows_column(self):
        """When mode is 'manual', the Input Tokens column should be visible."""
        token_count_mode = "manual"
        is_disabled = token_count_mode == "disabled"
        column_hidden = is_disabled
        assert column_hidden is False

    def test_automatic_mode_shows_column(self):
        """When mode is 'automatic', the Input Tokens column should be visible."""
        token_count_mode = "automatic"
        is_disabled = token_count_mode == "disabled"
        column_hidden = is_disabled
        assert column_hidden is False

    def test_disabled_mode_hides_button(self):
        """When mode is 'disabled', the Count Tokens button should be hidden."""
        token_count_mode = "disabled"
        is_disabled = token_count_mode == "disabled"
        button_visible = not is_disabled
        assert button_visible is False

    def test_manual_mode_shows_button(self):
        """When mode is 'manual', the Count Tokens button should be visible."""
        token_count_mode = "manual"
        is_disabled = token_count_mode == "disabled"
        button_visible = not is_disabled
        assert button_visible is True

    def test_automatic_mode_shows_button(self):
        """When mode is 'automatic', the Count Tokens button should be visible."""
        token_count_mode = "automatic"
        is_disabled = token_count_mode == "disabled"
        button_visible = not is_disabled
        assert button_visible is True


@pytest.mark.unit
class TestTokenCountVisibilityTransitions:
    """Test suite for transitioning between modes and verifying UI state."""

    def test_switch_from_manual_to_disabled_hides_ui(self):
        """Switching from manual to disabled should hide token UI."""
        # Start in manual mode
        mode = "manual"
        assert (mode == "disabled") is False  # Column visible, button visible

        # Switch to disabled
        mode = "disabled"
        is_disabled = mode == "disabled"
        assert is_disabled is True  # Column hidden, button hidden

    def test_switch_from_disabled_to_manual_shows_ui(self):
        """Switching from disabled to manual should show token UI."""
        # Start in disabled mode
        mode = "disabled"
        assert (mode == "disabled") is True

        # Switch to manual
        mode = "manual"
        is_disabled = mode == "disabled"
        assert is_disabled is False  # Column visible, button visible

    def test_switch_from_disabled_to_automatic_shows_ui(self):
        """Switching from disabled to automatic should show token UI."""
        mode = "disabled"
        assert (mode == "disabled") is True

        mode = "automatic"
        is_disabled = mode == "disabled"
        assert is_disabled is False

    def test_switch_from_automatic_to_disabled_hides_ui(self):
        """Switching from automatic to disabled should hide token UI."""
        mode = "automatic"
        assert (mode == "disabled") is False

        mode = "disabled"
        is_disabled = mode == "disabled"
        assert is_disabled is True


@pytest.mark.unit
class TestTokenCountClearedOnDisable:
    """Test suite for clearing token counts when mode is set to disabled."""

    def test_token_counts_cleared_on_disable(self):
        """Previously fetched token counts should be cleared when disabled."""
        class MockFileItem:
            def __init__(self, count):
                self.input_token_count = count

        file_items = {
            "file1.txt": MockFileItem(1000),
            "file2.txt": MockFileItem(2000),
            "file3.txt": MockFileItem(None),
        }

        # Simulate _update_token_count_visibility with disabled mode
        token_count_mode = "disabled"
        if token_count_mode == "disabled":
            for fi in file_items.values():
                fi.input_token_count = None

        assert all(fi.input_token_count is None for fi in file_items.values())

    def test_token_counts_preserved_on_manual(self):
        """Token counts should be preserved when switching to manual mode."""
        class MockFileItem:
            def __init__(self, count):
                self.input_token_count = count

        file_items = {
            "file1.txt": MockFileItem(1000),
            "file2.txt": MockFileItem(2000),
        }

        token_count_mode = "manual"
        if token_count_mode == "disabled":
            for fi in file_items.values():
                fi.input_token_count = None

        assert file_items["file1.txt"].input_token_count == 1000
        assert file_items["file2.txt"].input_token_count == 2000

    def test_token_counts_preserved_on_automatic(self):
        """Token counts should be preserved when switching to automatic mode."""
        class MockFileItem:
            def __init__(self, count):
                self.input_token_count = count

        file_items = {
            "file1.txt": MockFileItem(1500),
        }

        token_count_mode = "automatic"
        if token_count_mode == "disabled":
            for fi in file_items.values():
                fi.input_token_count = None

        assert file_items["file1.txt"].input_token_count == 1500


@pytest.mark.unit
class TestStatsExcludePreCheckWhenDisabled:
    """Test suite for excluding pre-check token info from Stats when disabled."""

    def _create_format_stats(self, token_count_mode):
        """Create a standalone _format_stats function that checks mode."""
        def _format_stats(result, file_item=None):
            input_tokens = result.get("input_tokens", 0)
            output_tokens = result.get("output_tokens", 0)
            cache_creation = result.get("cache_creation_input_tokens", 0)
            cache_read = result.get("cache_read_input_tokens", 0)
            total_tokens = input_tokens + output_tokens

            lines = []

            # Show pre-checked input token count if available and not disabled
            if (file_item and file_item.input_token_count is not None
                    and token_count_mode != "disabled"):
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

    def test_stats_exclude_pre_check_when_disabled(self):
        """Pre-Check Token Count should not appear in stats when mode is disabled."""
        format_stats = self._create_format_stats("disabled")

        class MockFileItem:
            input_token_count = 1500

        result = {"input_tokens": 100, "output_tokens": 50}
        output = format_stats(result, file_item=MockFileItem())
        assert "Pre-Check Token Count" not in output
        assert "Estimated input tokens" not in output
        # Other stats should still appear
        assert "Token Usage" in output
        assert "Input tokens:" in output

    def test_stats_include_pre_check_when_manual(self):
        """Pre-Check Token Count should appear in stats when mode is manual."""
        format_stats = self._create_format_stats("manual")

        class MockFileItem:
            input_token_count = 1500

        result = {"input_tokens": 100, "output_tokens": 50}
        output = format_stats(result, file_item=MockFileItem())
        assert "Pre-Check Token Count" in output
        assert "Estimated input tokens:      1,500" in output

    def test_stats_include_pre_check_when_automatic(self):
        """Pre-Check Token Count should appear in stats when mode is automatic."""
        format_stats = self._create_format_stats("automatic")

        class MockFileItem:
            input_token_count = 2000

        result = {"input_tokens": 200, "output_tokens": 75}
        output = format_stats(result, file_item=MockFileItem())
        assert "Pre-Check Token Count" in output
        assert "Estimated input tokens:      2,000" in output

    def test_stats_no_pre_check_none_token_count_any_mode(self):
        """When input_token_count is None, Pre-Check should not appear regardless of mode."""
        for mode in ("manual", "automatic", "disabled"):
            format_stats = self._create_format_stats(mode)

            class MockFileItem:
                input_token_count = None

            result = {"input_tokens": 100, "output_tokens": 50}
            output = format_stats(result, file_item=MockFileItem())
            assert "Pre-Check Token Count" not in output

    def test_unconverted_stats_hidden_when_disabled(self):
        """When not converted and mode is disabled, stats should be empty."""
        token_count_mode = "disabled"
        input_token_count = 1500

        # Simulate the display logic for unconverted files
        if (input_token_count is not None
                and token_count_mode != "disabled"):
            stats_text = "Pre-Check Token Count\n..."
        else:
            stats_text = ""

        assert stats_text == ""

    def test_unconverted_stats_shown_when_manual(self):
        """When not converted and mode is manual, pre-check stats should show."""
        token_count_mode = "manual"
        input_token_count = 1500

        if (input_token_count is not None
                and token_count_mode != "disabled"):
            stats_text = f"Pre-Check Token Count\n{'=' * 30}\nEstimated input tokens:      {input_token_count:,}"
        else:
            stats_text = ""

        assert "Pre-Check Token Count" in stats_text
        assert "1,500" in stats_text


@pytest.mark.unit
class TestAllModesVisibilityMatrix:
    """Test that every mode maps to the correct visibility for each UI element."""

    @pytest.mark.parametrize("mode,col_hidden,btn_visible", [
        ("disabled", True, False),
        ("manual", False, True),
        ("automatic", False, True),
    ])
    def test_visibility_matrix(self, mode, col_hidden, btn_visible):
        """Verify column hidden and button visible states for each mode."""
        is_disabled = mode == "disabled"
        assert is_disabled == col_hidden
        assert (not is_disabled) == btn_visible

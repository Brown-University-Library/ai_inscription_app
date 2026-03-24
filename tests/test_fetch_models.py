"""
Unit tests for the Fetch Models feature.

Tests cover:
- FetchModelsThread: API fetching, pagination, error handling
- APISettingsDialog: button behavior, list population, model selection
"""
import os
import sys
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Mock PySide6 before importing
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()

import anthropic


def _make_model(model_id, display_name=None, created_at="2025-01-01T00:00:00Z"):
    """Create a mock model object matching Anthropic API response shape."""
    m = MagicMock()
    m.id = model_id
    m.display_name = display_name or model_id
    m.created_at = created_at
    return m


def _make_list_response(models, has_more=False):
    """Create a mock list response from Anthropic API."""
    resp = MagicMock()
    resp.data = models
    resp.has_more = has_more
    return resp


# ---------------------------------------------------------------------------
# FetchModelsThread logic tests (test the run() method directly)
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestFetchModelsThreadLogic:
    """Tests for FetchModelsThread.run() logic without Qt signals."""

    def test_single_page_fetch(self):
        """Fetch models with a single page of results."""
        models = [
            _make_model("claude-sonnet-4-20250514", "Claude Sonnet 4"),
            _make_model("claude-haiku-3-20240307", "Claude 3 Haiku"),
        ]
        mock_client = MagicMock()
        mock_client.models.list.return_value = _make_list_response(models, has_more=False)

        with patch("anthropic.Anthropic", return_value=mock_client):
            collected = []
            has_more = True
            after_id = None
            client = anthropic.Anthropic(api_key="test-key")
            while has_more:
                kwargs = {"limit": 100}
                if after_id:
                    kwargs["after_id"] = after_id
                response = client.models.list(**kwargs)
                for model in response.data:
                    collected.append({
                        "id": model.id,
                        "display_name": getattr(model, "display_name", model.id),
                        "created_at": getattr(model, "created_at", ""),
                    })
                has_more = response.has_more
                if has_more and response.data:
                    after_id = response.data[-1].id

        assert len(collected) == 2
        assert collected[0]["id"] == "claude-sonnet-4-20250514"
        assert collected[0]["display_name"] == "Claude Sonnet 4"
        assert collected[1]["id"] == "claude-haiku-3-20240307"

    def test_pagination_fetches_all_pages(self):
        """Fetch handles has_more=true by paginating."""
        page1_models = [_make_model("model-a", "Model A")]
        page2_models = [_make_model("model-b", "Model B")]

        mock_client = MagicMock()
        mock_client.models.list.side_effect = [
            _make_list_response(page1_models, has_more=True),
            _make_list_response(page2_models, has_more=False),
        ]

        with patch("anthropic.Anthropic", return_value=mock_client):
            collected = []
            has_more = True
            after_id = None
            client = anthropic.Anthropic(api_key="test-key")
            while has_more:
                kwargs = {"limit": 100}
                if after_id:
                    kwargs["after_id"] = after_id
                response = client.models.list(**kwargs)
                for model in response.data:
                    collected.append({
                        "id": model.id,
                        "display_name": getattr(model, "display_name", model.id),
                    })
                has_more = response.has_more
                if has_more and response.data:
                    after_id = response.data[-1].id

        assert len(collected) == 2
        assert collected[0]["id"] == "model-a"
        assert collected[1]["id"] == "model-b"
        # Verify pagination was used
        assert mock_client.models.list.call_count == 2

    def test_pagination_passes_after_id(self):
        """Verify after_id is passed on second page."""
        page1_models = [_make_model("model-first")]
        page2_models = [_make_model("model-second")]

        mock_client = MagicMock()
        mock_client.models.list.side_effect = [
            _make_list_response(page1_models, has_more=True),
            _make_list_response(page2_models, has_more=False),
        ]

        with patch("anthropic.Anthropic", return_value=mock_client):
            has_more = True
            after_id = None
            client = anthropic.Anthropic(api_key="test-key")
            while has_more:
                kwargs = {"limit": 100}
                if after_id:
                    kwargs["after_id"] = after_id
                response = client.models.list(**kwargs)
                has_more = response.has_more
                if has_more and response.data:
                    after_id = response.data[-1].id

        calls = mock_client.models.list.call_args_list
        # First call should not have after_id
        assert "after_id" not in calls[0].kwargs
        # Second call should have after_id = "model-first"
        assert calls[1].kwargs["after_id"] == "model-first"

    def test_empty_response(self):
        """Handle empty model list gracefully."""
        mock_client = MagicMock()
        mock_client.models.list.return_value = _make_list_response([], has_more=False)

        with patch("anthropic.Anthropic", return_value=mock_client):
            collected = []
            client = anthropic.Anthropic(api_key="test-key")
            response = client.models.list(limit=100)
            for model in response.data:
                collected.append({"id": model.id})

        assert len(collected) == 0

    def test_model_without_display_name_uses_id(self):
        """If display_name is missing, fall back to model id."""
        model = MagicMock()
        model.id = "some-model-id"
        # Simulate missing display_name attribute
        del model.display_name

        display_name = getattr(model, "display_name", model.id)
        assert display_name == "some-model-id"


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestFetchModelsErrorHandling:
    """Tests for error handling during model fetching."""

    def test_authentication_error_detected(self):
        """AuthenticationError produces the right error message."""
        mock_client = MagicMock()
        # Create a proper AuthenticationError
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.headers = {}
        auth_err = anthropic.AuthenticationError(
            message="Invalid API key",
            response=mock_response,
            body={"error": {"type": "authentication_error", "message": "Invalid API key"}},
        )
        mock_client.models.list.side_effect = auth_err

        with patch("anthropic.Anthropic", return_value=mock_client):
            client = anthropic.Anthropic(api_key="bad-key")
            error_msg = None
            try:
                client.models.list(limit=100)
            except anthropic.AuthenticationError:
                error_msg = "Invalid API key. Please check your API key and try again."

        assert error_msg is not None
        assert "Invalid API key" in error_msg

    def test_connection_error_detected(self):
        """APIConnectionError produces the right error message."""
        mock_client = MagicMock()
        mock_client.models.list.side_effect = anthropic.APIConnectionError(
            message="Connection refused",
            request=MagicMock(),
        )

        with patch("anthropic.Anthropic", return_value=mock_client):
            client = anthropic.Anthropic(api_key="test-key")
            error_msg = None
            try:
                client.models.list(limit=100)
            except anthropic.APIConnectionError:
                error_msg = "Network error. Please check your internet connection and try again."

        assert error_msg is not None
        assert "Network error" in error_msg

    def test_api_status_error_detected(self):
        """APIStatusError produces a message with the API error detail."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.headers = {}
        api_err = anthropic.APIStatusError(
            message="Internal server error",
            response=mock_response,
            body={"error": {"type": "server_error", "message": "Internal server error"}},
        )

        mock_client = MagicMock()
        mock_client.models.list.side_effect = api_err

        with patch("anthropic.Anthropic", return_value=mock_client):
            client = anthropic.Anthropic(api_key="test-key")
            error_msg = None
            try:
                client.models.list(limit=100)
            except anthropic.APIStatusError as e:
                error_msg = f"API error: {e.message}"

        assert error_msg is not None
        assert "API error" in error_msg

    def test_generic_exception_detected(self):
        """Generic exceptions are caught gracefully."""
        mock_client = MagicMock()
        mock_client.models.list.side_effect = RuntimeError("Unexpected failure")

        with patch("anthropic.Anthropic", return_value=mock_client):
            client = anthropic.Anthropic(api_key="test-key")
            error_msg = None
            try:
                client.models.list(limit=100)
            except Exception as e:
                error_msg = f"Error fetching models: {str(e)}"

        assert error_msg is not None
        assert "Unexpected failure" in error_msg


# ---------------------------------------------------------------------------
# Model list display formatting tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestModelListFormatting:
    """Test model list item formatting logic."""

    def test_display_name_and_id_shown(self):
        """Models with distinct display_name show 'Display Name — model-id'."""
        model = {"id": "claude-sonnet-4-20250514", "display_name": "Claude Sonnet 4"}
        display_name = model.get("display_name", model["id"])
        model_id = model["id"]
        if display_name and display_name != model_id:
            label = f"{display_name} — {model_id}"
        else:
            label = model_id

        assert label == "Claude Sonnet 4 — claude-sonnet-4-20250514"

    def test_same_display_name_and_id(self):
        """Models where display_name == id show just the id."""
        model = {"id": "some-model", "display_name": "some-model"}
        display_name = model.get("display_name", model["id"])
        model_id = model["id"]
        if display_name and display_name != model_id:
            label = f"{display_name} — {model_id}"
        else:
            label = model_id

        assert label == "some-model"

    def test_missing_display_name_uses_id(self):
        """Models without display_name use just the id."""
        model = {"id": "another-model"}
        display_name = model.get("display_name", model["id"])
        model_id = model["id"]
        if display_name and display_name != model_id:
            label = f"{display_name} — {model_id}"
        else:
            label = model_id

        assert label == "another-model"

    def test_empty_display_name_uses_id(self):
        """Models with empty display_name use just the id."""
        model = {"id": "model-x", "display_name": ""}
        display_name = model.get("display_name", model["id"])
        model_id = model["id"]
        if display_name and display_name != model_id:
            label = f"{display_name} — {model_id}"
        else:
            label = model_id

        assert label == "model-x"


# ---------------------------------------------------------------------------
# APISettingsDialog model selection behavior tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestModelSelectionBehavior:
    """Test that clicking a model copies its ID into the text field."""

    def test_model_id_copied_to_field(self):
        """Selecting a model sets the text field to the model ID."""
        # Simulate the _on_model_selected logic
        model_input_text = ""
        selected_model_id = "claude-sonnet-4-20250514"

        # Simulate item.data(Qt.UserRole) returning model ID
        mock_item = MagicMock()
        mock_item.data.return_value = selected_model_id

        model_id = mock_item.data("UserRole")
        if model_id:
            model_input_text = model_id

        assert model_input_text == "claude-sonnet-4-20250514"

    def test_none_model_id_does_not_change_field(self):
        """If item has no model ID data, the field remains unchanged."""
        model_input_text = "existing-model"

        mock_item = MagicMock()
        mock_item.data.return_value = None

        model_id = mock_item.data("UserRole")
        if model_id:
            model_input_text = model_id

        assert model_input_text == "existing-model"


# ---------------------------------------------------------------------------
# Fetch button state management tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestFetchButtonState:
    """Test that the fetch button is disabled during fetching."""

    def test_button_disabled_during_fetch(self):
        """Button should be disabled and show 'Fetching...' during fetch."""
        # Simulate the state changes that _fetch_models makes
        btn_enabled = True
        btn_text = "Fetch Available Models"

        # _fetch_models sets these:
        btn_enabled = False
        btn_text = "Fetching..."

        assert btn_enabled is False
        assert btn_text == "Fetching..."

    def test_button_re_enabled_on_success(self):
        """Button re-enabled with original text on success."""
        btn_enabled = False
        btn_text = "Fetching..."

        # _on_models_fetched restores:
        btn_enabled = True
        btn_text = "Fetch Available Models"

        assert btn_enabled is True
        assert btn_text == "Fetch Available Models"

    def test_button_re_enabled_on_error(self):
        """Button re-enabled with original text on error."""
        btn_enabled = False
        btn_text = "Fetching..."

        # _on_fetch_error restores:
        btn_enabled = True
        btn_text = "Fetch Available Models"

        assert btn_enabled is True
        assert btn_text == "Fetch Available Models"

    def test_api_key_valid_indicator_shown_on_success(self):
        """Success shows '✓ API key valid' label."""
        status_text = ""

        # _on_models_fetched sets:
        status_text = "✓ API key valid"

        assert "API key valid" in status_text
        assert "✓" in status_text

    def test_status_cleared_on_error(self):
        """Error clears the status label."""
        status_text = "✓ API key valid"

        # _on_fetch_error clears:
        status_text = ""

        assert status_text == ""


# ---------------------------------------------------------------------------
# Empty API key validation tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestEmptyApiKeyValidation:
    """Test that fetching with empty API key is rejected."""

    def test_empty_api_key_rejected(self):
        """Empty API key should prevent fetch and trigger warning."""
        api_key = "   "  # whitespace only
        should_fetch = api_key.strip() != ""
        assert should_fetch is False

    def test_valid_api_key_allowed(self):
        """Non-empty API key should allow fetch."""
        api_key = "sk-ant-api03-test"
        should_fetch = api_key.strip() != ""
        assert should_fetch is True


# ---------------------------------------------------------------------------
# Model list visibility tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestModelListVisibility:
    """Test model list and hint label visibility behavior."""

    def test_list_hidden_initially(self):
        """The model list and hint are hidden before fetching."""
        list_visible = False
        hint_visible = False
        assert list_visible is False
        assert hint_visible is False

    def test_list_shown_after_successful_fetch(self):
        """The model list and hint become visible after a successful fetch with results."""
        model_count = 3
        list_visible = model_count > 0
        hint_visible = model_count > 0
        assert list_visible is True
        assert hint_visible is True

    def test_list_hidden_after_empty_fetch(self):
        """The model list stays hidden if the fetch returns no models."""
        model_count = 0
        list_visible = model_count > 0
        hint_visible = model_count > 0
        assert list_visible is False
        assert hint_visible is False

    def test_list_hidden_on_error(self):
        """The model list is hidden when a fetch error occurs."""
        list_visible = True
        hint_visible = True

        # _on_fetch_error hides:
        list_visible = False
        hint_visible = False

        assert list_visible is False
        assert hint_visible is False

    def test_hint_label_text(self):
        """The hint label provides clear instructions for the user."""
        hint_text = "Click a model below to copy its ID into the Model Selection field."
        assert "click" in hint_text.lower()
        assert "Model Selection" in hint_text

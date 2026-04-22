"""
Unit tests for intelligent prompt caching during batch conversions.
"""
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _dummy_class(name):
    """Create a minimal Qt-compatible dummy class."""
    return type(name, (), {"__init__": lambda self, *args, **kwargs: None})


class DummySignal:
    """Minimal replacement for PySide6.QtCore.Signal."""

    def __init__(self, *args, **kwargs):
        pass

    def emit(self, *args, **kwargs):
        pass

    def connect(self, *args, **kwargs):
        pass


dummy_widgets = types.SimpleNamespace(
    QApplication=_dummy_class("QApplication"),
    QMainWindow=_dummy_class("QMainWindow"),
    QWidget=_dummy_class("QWidget"),
    QVBoxLayout=_dummy_class("QVBoxLayout"),
    QHBoxLayout=_dummy_class("QHBoxLayout"),
    QTextEdit=_dummy_class("QTextEdit"),
    QPushButton=_dummy_class("QPushButton"),
    QLabel=_dummy_class("QLabel"),
    QFileDialog=_dummy_class("QFileDialog"),
    QDialog=_dummy_class("QDialog"),
    QLineEdit=_dummy_class("QLineEdit"),
    QFormLayout=_dummy_class("QFormLayout"),
    QMessageBox=_dummy_class("QMessageBox"),
    QSplitter=_dummy_class("QSplitter"),
    QInputDialog=_dummy_class("QInputDialog"),
    QTabWidget=_dummy_class("QTabWidget"),
    QRadioButton=_dummy_class("QRadioButton"),
    QButtonGroup=_dummy_class("QButtonGroup"),
    QTableWidget=_dummy_class("QTableWidget"),
    QTableWidgetItem=_dummy_class("QTableWidgetItem"),
    QHeaderView=_dummy_class("QHeaderView"),
    QAbstractItemView=_dummy_class("QAbstractItemView"),
    QGridLayout=_dummy_class("QGridLayout"),
    QComboBox=_dummy_class("QComboBox"),
    QListWidget=_dummy_class("QListWidget"),
    QListWidgetItem=_dummy_class("QListWidgetItem"),
)
dummy_core = types.SimpleNamespace(
    QThread=_dummy_class("QThread"),
    Signal=DummySignal,
    Qt=types.SimpleNamespace(UserRole=0),
)
dummy_gui = types.SimpleNamespace(
    QAction=_dummy_class("QAction"),
    QColor=_dummy_class("QColor"),
    QFont=_dummy_class("QFont"),
)


# Mock PySide6 before importing the application module
sys.modules['PySide6'] = types.SimpleNamespace()
sys.modules['PySide6.QtWidgets'] = dummy_widgets
sys.modules['PySide6.QtCore'] = dummy_core
sys.modules['PySide6.QtGui'] = dummy_gui


MODULE_PATH = next(Path(__file__).resolve().parents[1].glob("leiden-*.py"))


def load_app_module():
    """Load the application module from the hyphenated script filename."""
    module_name = "leiden_epidoc_app"
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def make_response(cache_creation_tokens=0, cache_read_tokens=0):
    """Create a mocked Anthropic response with token usage metadata."""
    response = MagicMock()
    content = MagicMock()
    content.text = (
        "<analysis>Batch analysis</analysis>"
        "<notes>Batch notes</notes>"
        "<final_translation><lb/>Batch translation</final_translation>"
    )
    response.content = [content]
    response.usage = MagicMock(
        input_tokens=200,
        output_tokens=80,
        cache_creation_input_tokens=cache_creation_tokens,
        cache_read_input_tokens=cache_read_tokens,
    )
    response.stop_reason = "end_turn"
    return response


@pytest.mark.unit
class TestPromptCaching:
    """Test suite for prompt caching request construction and batch usage."""

    def test_prompt_cache_threshold_defaults_to_two(self, tmp_path, monkeypatch):
        """Prompt caching should default to batches of two or more documents."""
        monkeypatch.chdir(tmp_path)
        module = load_app_module()

        converter = module.LeidenToEpiDocConverter()

        assert converter.prompt_cache_batch_threshold == 2
        assert converter.should_use_prompt_cache(1) is False
        assert converter.should_use_prompt_cache(2) is True

    def test_build_request_params_bypass_cache_for_single_message(self, tmp_path, monkeypatch):
        """Single conversions should keep the uncached payload shape."""
        monkeypatch.chdir(tmp_path)
        module = load_app_module()
        converter = module.LeidenToEpiDocConverter()

        system_prompt, messages = converter._build_request_params("single item", batch_size=1)

        assert isinstance(system_prompt, str)
        assert len(messages[0]["content"]) == 1
        assert "cache_control" not in messages[0]["content"][0]
        assert "single item" in messages[0]["content"][0]["text"]

    def test_build_request_params_enable_cache_for_batch(self, tmp_path, monkeypatch):
        """Batch conversions should cache the reusable prompt prefix."""
        monkeypatch.chdir(tmp_path)
        module = load_app_module()
        converter = module.LeidenToEpiDocConverter()

        system_prompt, messages = converter._build_request_params("batched item", batch_size=2)

        assert isinstance(system_prompt, list)
        assert system_prompt[0]["cache_control"] == {"type": "ephemeral"}
        assert len(messages[0]["content"]) == 2
        assert messages[0]["content"][0]["cache_control"] == {"type": "ephemeral"}
        assert "batched item" in messages[0]["content"][1]["text"]
        assert "cache_control" not in messages[0]["content"][1]

    def test_get_epidoc_uses_cached_payload_for_batched_requests(self, tmp_path, monkeypatch):
        """Batched requests should send cached prompt blocks and capture cache stats."""
        monkeypatch.chdir(tmp_path)
        module = load_app_module()
        converter = module.LeidenToEpiDocConverter()
        converter.api_key = "test-key"

        mock_client = MagicMock()
        mock_client.messages.create.return_value = make_response(
            cache_creation_tokens=120,
            cache_read_tokens=40,
        )

        with patch.object(module.anthropic, "Anthropic", return_value=mock_client):
            result = converter.get_epidoc("batch text", batch_size=2)

        create_kwargs = mock_client.messages.create.call_args.kwargs
        assert isinstance(create_kwargs["system"], list)
        assert create_kwargs["messages"][0]["content"][0]["cache_control"] == {"type": "ephemeral"}
        assert result["cache_creation_input_tokens"] == 120
        assert result["cache_read_input_tokens"] == 40

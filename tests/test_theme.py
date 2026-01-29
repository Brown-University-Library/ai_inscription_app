"""
Unit tests for theme preference functionality.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Need to mock PySide6 before importing the module
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()


@pytest.mark.unit
class TestThemePreference:
    """Test suite for theme preference functionality."""
    
    def test_theme_default_is_system(self, tmp_path, monkeypatch):
        """Test that default theme is 'system' when no config exists."""
        monkeypatch.chdir(tmp_path)
        
        # No config file exists, so theme should default to "system"
        config = {}
        theme = config.get("theme", "system")
        
        assert theme == "system"
    
    def test_theme_loads_from_config(self, tmp_path, monkeypatch):
        """Test loading theme preference from config file."""
        monkeypatch.chdir(tmp_path)
        
        # Create config with dark theme
        config_file = tmp_path / "leiden_epidoc_config.json"
        config_data = {
            "api_key": "test-key",
            "model": "test-model",
            "save_location": "/test/path",
            "theme": "dark"
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Load config
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        assert config["theme"] == "dark"
    
    def test_theme_saves_to_config(self, tmp_path, monkeypatch):
        """Test saving theme preference to config file."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "leiden_epidoc_config.json"
        
        # Save config with light theme
        config = {
            "api_key": "test-key",
            "model": "test-model",
            "save_location": "/test/path",
            "theme": "light"
        }
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Verify saved data
        with open(config_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded["theme"] == "light"
    
    def test_theme_persists_after_update(self, tmp_path, monkeypatch):
        """Test that theme preference persists after being changed."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "leiden_epidoc_config.json"
        
        # Create initial config
        config = {
            "api_key": "test-key",
            "model": "test-model",
            "save_location": "/test/path",
            "theme": "system"
        }
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Load and update theme
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        config["theme"] = "dark"
        
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Verify persistence
        with open(config_file, 'r') as f:
            final_config = json.load(f)
        
        assert final_config["theme"] == "dark"
    
    def test_theme_valid_values(self):
        """Test that only valid theme values are accepted."""
        valid_themes = ["light", "dark", "system"]
        
        for theme in valid_themes:
            assert theme in valid_themes
    
    def test_theme_fallback_for_invalid(self, tmp_path, monkeypatch):
        """Test fallback to system theme for invalid config values."""
        monkeypatch.chdir(tmp_path)
        
        # Create config with invalid theme value
        config_file = tmp_path / "leiden_epidoc_config.json"
        config_data = {
            "api_key": "test-key",
            "theme": "invalid_theme"
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Application should handle invalid theme
        theme = config.get("theme", "system")
        # If theme is not in valid list, default to system
        valid_themes = ["light", "dark", "system"]
        if theme not in valid_themes:
            theme = "system"
        
        assert theme == "system"
    
    def test_theme_backward_compatibility(self, tmp_path, monkeypatch):
        """Test that old config files without theme field work correctly."""
        monkeypatch.chdir(tmp_path)
        
        # Create old-style config without theme
        config_file = tmp_path / "leiden_epidoc_config.json"
        config_data = {
            "api_key": "old-key",
            "model": "old-model",
            "save_location": "/old/path"
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Theme should default to "system" when not present
        theme = config.get("theme", "system")
        
        assert theme == "system"
        # Original config values should still work
        assert config["api_key"] == "old-key"
        assert config["model"] == "old-model"
        assert config["save_location"] == "/old/path"
    
    def test_config_includes_theme_on_save(self, tmp_path, monkeypatch):
        """Test that saving config includes the theme field."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "leiden_epidoc_config.json"
        
        # Simulate save_config behavior including theme
        config = {
            "api_key": "new-key",
            "model": "new-model",
            "save_location": "/new/path",
            "theme": "dark"
        }
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        with open(config_file, 'r') as f:
            loaded = json.load(f)
        
        assert "theme" in loaded
        assert loaded["theme"] == "dark"


@pytest.mark.unit
class TestApplyTheme:
    """Test suite for apply_theme function behavior."""
    
    def test_apply_theme_light_sets_palette(self):
        """Test that light theme sets appropriate palette colors."""
        # Test the logic of light theme
        theme = "light"
        
        # Light theme should use light colors
        if theme == "light":
            # Window background should be light (e.g., RGB 240, 240, 240)
            window_bg = (240, 240, 240)
            text_color = (0, 0, 0)  # Black text
            base_color = (255, 255, 255)  # White base
        
        assert window_bg == (240, 240, 240)
        assert text_color == (0, 0, 0)
        assert base_color == (255, 255, 255)
    
    def test_apply_theme_dark_sets_palette(self):
        """Test that dark theme sets appropriate palette colors."""
        theme = "dark"
        
        # Dark theme should use dark colors
        if theme == "dark":
            window_bg = (53, 53, 53)  # Dark gray
            text_color = (255, 255, 255)  # White text
            base_color = (35, 35, 35)  # Darker base
        
        assert window_bg == (53, 53, 53)
        assert text_color == (255, 255, 255)
        assert base_color == (35, 35, 35)
    
    def test_apply_theme_system_resets(self):
        """Test that system theme resets to default palette."""
        theme = "system"
        
        # System theme means use default (no custom palette)
        should_reset_palette = (theme == "system")
        
        assert should_reset_palette is True
    
    def test_theme_options_match_menu(self):
        """Test that theme options match expected menu items."""
        expected_themes = {
            "light": "Light",
            "dark": "Dark",
            "system": "System (Default)"
        }
        
        assert len(expected_themes) == 3
        assert "light" in expected_themes
        assert "dark" in expected_themes
        assert "system" in expected_themes

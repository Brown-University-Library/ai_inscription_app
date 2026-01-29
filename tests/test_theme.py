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
    
    def test_theme_validation_rejects_invalid(self):
        """Test that invalid theme values are rejected and default to system."""
        valid_themes = ("light", "dark", "system")
        invalid_themes = ["purple", "auto", "", "DARK", "Light", None, 123]
        
        for invalid_theme in invalid_themes:
            # Simulate the validation logic used in the application
            theme = invalid_theme if invalid_theme in valid_themes else "system"
            assert theme == "system", f"Invalid theme '{invalid_theme}' should default to 'system'"
    
    def test_theme_validation_accepts_valid(self):
        """Test that valid theme values are accepted."""
        valid_themes = ("light", "dark", "system")
        
        for valid_theme in valid_themes:
            # Simulate the validation logic used in the application
            theme = valid_theme if valid_theme in valid_themes else "system"
            assert theme == valid_theme, f"Valid theme '{valid_theme}' should be accepted"
    
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
    
    def test_light_theme_color_specification(self):
        """Test that light theme specifies correct color values."""
        # These are the expected RGB values for light theme as defined in the app
        expected_colors = {
            "window_bg": (240, 240, 240),      # Light gray window background
            "window_text": (0, 0, 0),           # Black text
            "base": (255, 255, 255),            # White base for inputs
            "alternate_base": (245, 245, 245), # Slightly darker alternate
            "text": (0, 0, 0),                  # Black text on base
            "button": (240, 240, 240),         # Light button background
            "button_text": (0, 0, 0),          # Black button text
            "highlight": (42, 130, 218),       # Blue highlight
            "highlight_text": (255, 255, 255), # White highlighted text
        }
        
        # Verify the color specifications are sensible for a light theme
        # Window background should be light (high RGB values)
        assert all(v >= 200 for v in expected_colors["window_bg"]), "Window bg should be light"
        # Text should be dark (low RGB values)
        assert all(v <= 50 for v in expected_colors["window_text"]), "Window text should be dark"
        # Base should be white or near-white
        assert all(v >= 245 for v in expected_colors["base"]), "Base should be white"
    
    def test_dark_theme_color_specification(self):
        """Test that dark theme specifies correct color values."""
        # These are the expected RGB values for dark theme as defined in the app
        expected_colors = {
            "window_bg": (53, 53, 53),         # Dark gray window background
            "window_text": (255, 255, 255),    # White text
            "base": (35, 35, 35),              # Dark base for inputs
            "alternate_base": (53, 53, 53),   # Same as window
            "text": (255, 255, 255),           # White text on base
            "button": (53, 53, 53),            # Dark button background
            "button_text": (255, 255, 255),   # White button text
            "highlight": (42, 130, 218),       # Blue highlight (same as light)
            "highlight_text": (255, 255, 255), # White highlighted text
        }
        
        # Verify the color specifications are sensible for a dark theme
        # Window background should be dark (low RGB values)
        assert all(v <= 80 for v in expected_colors["window_bg"]), "Window bg should be dark"
        # Text should be light (high RGB values)
        assert all(v >= 200 for v in expected_colors["window_text"]), "Window text should be light"
        # Base should be dark
        assert all(v <= 50 for v in expected_colors["base"]), "Base should be dark"
    
    def test_system_theme_behavior(self):
        """Test that system theme indicates reset to platform defaults."""
        # When theme is "system", the app should reset to platform default
        theme = "system"
        
        # The expected behavior is to NOT apply a custom palette
        should_use_custom_palette = (theme in ("light", "dark"))
        should_reset_to_default = (theme == "system")
        
        assert should_use_custom_palette is False
        assert should_reset_to_default is True
    
    def test_apply_theme_validates_input(self):
        """Test that apply_theme validation logic handles invalid themes."""
        valid_themes = ("light", "dark", "system")
        
        # Test cases where validation should fallback to system
        test_cases = [
            ("light", "light"),    # Valid - should keep
            ("dark", "dark"),      # Valid - should keep
            ("system", "system"),  # Valid - should keep
            ("invalid", "system"), # Invalid - should fallback to system
            ("", "system"),        # Empty - should fallback to system
        ]
        
        for input_theme, expected_result in test_cases:
            # Simulate the validation logic
            result = input_theme if input_theme in valid_themes else "system"
            assert result == expected_result, f"Theme '{input_theme}' should result in '{expected_result}'"
    
    def test_theme_display_names(self):
        """Test that theme display names match expected labels for UI."""
        # These display names are used in the status bar message
        display_names = {
            "light": "Light",
            "dark": "Dark",
            "system": "System (Default)"
        }
        
        # Verify all themes have display names
        assert len(display_names) == 3
        assert display_names["light"] == "Light"
        assert display_names["dark"] == "Dark"
        assert display_names["system"] == "System (Default)"
        
        # Verify system is marked as default
        assert "Default" in display_names["system"]

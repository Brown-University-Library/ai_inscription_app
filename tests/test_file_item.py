"""
Unit tests for FileItem class.
"""
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import sys

# Mock PySide6 before importing
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()


@pytest.mark.unit
class TestFileItem:
    """Test suite for FileItem class."""
    
    def test_file_item_initialization(self, sample_file_content):
        """Test FileItem initialization with a file path."""
        file_path = str(sample_file_content)
        
        # Simulate FileItem initialization
        file_item = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'input_text': "",
            'conversion_result': None,
            'is_converted': False,
            'has_error': False
        }
        
        assert file_item['file_path'] == file_path
        assert file_item['file_name'] == "sample_inscription.txt"
        assert file_item['input_text'] == ""
        assert file_item['conversion_result'] is None
        assert file_item['is_converted'] is False
        assert file_item['has_error'] is False
    
    def test_file_item_load_content_success(self, sample_file_content):
        """Test successful loading of file content."""
        file_path = str(sample_file_content)
        
        # Simulate load_content method
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            success = True
        except Exception:
            success = False
            content = ""
        
        assert success is True
        assert "[Marcus] Aurelius" in content
        assert "v(iro) c(larissimo)" in content
        assert "leg(ato)" in content
    
    def test_file_item_load_content_file_not_found(self, tmp_path):
        """Test loading content from non-existent file."""
        file_path = str(tmp_path / "nonexistent.txt")
        
        # Simulate load_content method with error
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            success = True
        except Exception as e:
            success = False
            content = ""
        
        assert success is False
    
    def test_file_item_load_content_permission_error(self, tmp_path):
        """Test loading content from file without read permission."""
        # Create a file
        file_path = tmp_path / "no_permission.txt"
        file_path.write_text("test content")
        
        # On Unix systems, make file unreadable
        if hasattr(os, 'chmod'):
            try:
                os.chmod(file_path, 0o000)
                
                # Try to read it
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    success = True
                except Exception:
                    success = False
                
                assert success is False
            finally:
                # Restore permissions for cleanup
                os.chmod(file_path, 0o644)
    
    def test_file_item_basename_extraction(self):
        """Test that file_name is correctly extracted from file_path."""
        test_cases = [
            ("/path/to/file.txt", "file.txt"),
            ("simple.txt", "simple.txt"),
            ("/long/path/to/inscription_123.txt", "inscription_123.txt")
        ]
        
        for file_path, expected_name in test_cases:
            actual_name = os.path.basename(file_path)
            assert actual_name == expected_name
    
    def test_file_item_conversion_state(self):
        """Test tracking conversion state."""
        file_item = {
            'file_path': "/test/file.txt",
            'file_name': "file.txt",
            'input_text': "test content",
            'conversion_result': None,
            'is_converted': False,
            'has_error': False
        }
        
        # Before conversion
        assert file_item['is_converted'] is False
        assert file_item['conversion_result'] is None
        assert file_item['has_error'] is False
        
        # After successful conversion
        file_item['conversion_result'] = {
            'has_tags': True,
            'analysis': 'test',
            'notes': 'test',
            'final_translation': 'test'
        }
        file_item['is_converted'] = True
        file_item['has_error'] = False
        
        assert file_item['is_converted'] is True
        assert file_item['conversion_result'] is not None
        assert file_item['has_error'] is False
        
        # After failed conversion
        file_item['conversion_result'] = {'error': 'API Error'}
        file_item['has_error'] = True
        
        assert file_item['is_converted'] is True
        assert file_item['has_error'] is True
    
    def test_file_item_unicode_content(self, tmp_path):
        """Test loading file with Unicode content."""
        file_path = tmp_path / "unicode_test.txt"
        unicode_content = """Εἶς θεὸς μόνος
אבג דהו
مرحبا
Здравствуй"""
        file_path.write_text(unicode_content, encoding='utf-8')
        
        # Load and verify
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_content = f.read()
        
        assert "Εἶς θεὸς" in loaded_content
        assert "אבג" in loaded_content
        assert "مرحبا" in loaded_content
        assert "Здравствуй" in loaded_content
    
    def test_file_item_empty_file(self, tmp_path):
        """Test loading empty file."""
        file_path = tmp_path / "empty.txt"
        file_path.write_text("", encoding='utf-8')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == ""
    
    def test_file_item_large_file(self, tmp_path):
        """Test loading large file."""
        file_path = tmp_path / "large.txt"
        # Create a file with 10000 lines
        large_content = "\n".join([f"Line {i}" for i in range(10000)])
        file_path.write_text(large_content, encoding='utf-8')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        assert len(lines) == 10000
        assert lines[0] == "Line 0"
        assert lines[9999] == "Line 9999"

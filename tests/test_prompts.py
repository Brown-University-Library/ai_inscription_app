"""
Unit tests for leiden_prompts module.
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from leiden_prompts import SYSTEM_INSTRUCTION, EXAMPLES_TEXT


@pytest.mark.unit
class TestLeidenPrompts:
    """Test suite for leiden_prompts module."""
    
    def test_system_instruction_exists(self):
        """Test that SYSTEM_INSTRUCTION constant exists and is not empty."""
        assert SYSTEM_INSTRUCTION is not None
        assert isinstance(SYSTEM_INSTRUCTION, str)
        assert len(SYSTEM_INSTRUCTION) > 0
    
    def test_examples_text_exists(self):
        """Test that EXAMPLES_TEXT constant exists and is not empty."""
        assert EXAMPLES_TEXT is not None
        assert isinstance(EXAMPLES_TEXT, str)
        assert len(EXAMPLES_TEXT) > 0
    
    def test_system_instruction_contains_key_sections(self):
        """Test that SYSTEM_INSTRUCTION contains expected sections."""
        # Check for key instruction sections
        assert "<instruction>" in SYSTEM_INSTRUCTION
        
        # Check for key concepts
        assert "Leiden Convention" in SYSTEM_INSTRUCTION or "Leiden convention" in SYSTEM_INSTRUCTION.lower()
        assert "EpiDoc" in SYSTEM_INSTRUCTION
        assert "XML" in SYSTEM_INSTRUCTION
    
    def test_system_instruction_contains_response_format(self):
        """Test that SYSTEM_INSTRUCTION specifies response format."""
        # Check for required tags in response format
        assert "<analysis>" in SYSTEM_INSTRUCTION
        assert "<notes>" in SYSTEM_INSTRUCTION
        assert "<final_translation>" in SYSTEM_INSTRUCTION
    
    def test_system_instruction_contains_leiden_conventions(self):
        """Test that SYSTEM_INSTRUCTION contains Leiden convention examples."""
        # Check for some common Leiden conventions
        conventions = [
            "Abbreviation",
            "Lost Letters",
            "Unclear Letters",
            "Supplied",
            "Line break",
            "Deletion"
        ]
        
        # At least some of these should be in the instruction
        found_conventions = sum(1 for conv in conventions if conv in SYSTEM_INSTRUCTION)
        assert found_conventions >= 3, "Should contain multiple Leiden convention examples"
    
    def test_system_instruction_contains_epidoc_tags(self):
        """Test that SYSTEM_INSTRUCTION contains EpiDoc XML tag examples."""
        # Check for common EpiDoc tags
        epidoc_tags = [
            "<supplied",
            "<expan>",
            "<abbr>",
            "<gap",
            "<lb",
            "<unclear>",
            "<del"
        ]
        
        # At least some of these should be in the instruction
        found_tags = sum(1 for tag in epidoc_tags if tag in SYSTEM_INSTRUCTION)
        assert found_tags >= 4, "Should contain multiple EpiDoc tag examples"
    
    def test_examples_text_structure(self):
        """Test that EXAMPLES_TEXT has proper structure."""
        assert "<examples>" in EXAMPLES_TEXT or "<example>" in EXAMPLES_TEXT
        assert "<Input>" in EXAMPLES_TEXT or "<input>" in EXAMPLES_TEXT.lower()
    
    def test_examples_text_contains_leiden_input(self):
        """Test that examples contain Leiden convention text."""
        # The examples should show actual Leiden text with conventions
        # Check for square brackets (common in Leiden)
        assert "[" in EXAMPLES_TEXT and "]" in EXAMPLES_TEXT
    
    def test_examples_text_contains_epidoc_output(self):
        """Test that examples contain EpiDoc XML output."""
        # Check for XML tags in examples
        assert "<" in EXAMPLES_TEXT and ">" in EXAMPLES_TEXT
        
        # Check for specific EpiDoc elements
        has_epidoc = (
            "<supplied" in EXAMPLES_TEXT or
            "<expan>" in EXAMPLES_TEXT or
            "<lb" in EXAMPLES_TEXT
        )
        assert has_epidoc, "Examples should contain EpiDoc XML"
    
    def test_system_instruction_whitespace_handling(self):
        """Test that instruction doesn't have excessive whitespace."""
        # Should not start or end with excessive whitespace
        assert not SYSTEM_INSTRUCTION.startswith("  ")
        assert not SYSTEM_INSTRUCTION.endswith("  ")
    
    def test_examples_whitespace_handling(self):
        """Test that examples don't have excessive whitespace."""
        # Should not start or end with excessive whitespace
        assert not EXAMPLES_TEXT.startswith("  ")
        assert not EXAMPLES_TEXT.endswith("  ")
    
    def test_system_instruction_important_warnings(self):
        """Test that instruction contains important warnings/notes."""
        # Check for the IMPORTANT note about single words
        assert "IMPORTANT" in SYSTEM_INSTRUCTION or "Important" in SYSTEM_INSTRUCTION
        
        # Check for guidance about spaces in tags
        assert "space" in SYSTEM_INSTRUCTION.lower() or "whitespace" in SYSTEM_INSTRUCTION.lower()
    
    def test_system_instruction_unicode_support(self):
        """Test that instruction mentions or shows Unicode/multilingual support."""
        # Check for non-Latin scripts in examples
        has_unicode = any(
            script in SYSTEM_INSTRUCTION
            for script in ["Greek", "Hebrew", "Arabic", "Coptic"]
        )
        assert has_unicode, "Should mention support for various scripts"
    
    def test_examples_greek_text(self):
        """Test that examples contain Greek text."""
        # Greek Unicode range check
        has_greek = any(ord(char) >= 0x0370 and ord(char) <= 0x03FF for char in EXAMPLES_TEXT)
        assert has_greek, "Examples should contain Greek text"
    
    def test_system_instruction_response_format_complete(self):
        """Test that response format instructions are complete."""
        # All three required sections should be documented
        assert "analysis" in SYSTEM_INSTRUCTION.lower()
        assert "notes" in SYSTEM_INSTRUCTION.lower()
        assert "final_translation" in SYSTEM_INSTRUCTION.lower() or "translation" in SYSTEM_INSTRUCTION.lower()
    
    def test_constants_are_strings(self):
        """Test that both constants are strings."""
        assert isinstance(SYSTEM_INSTRUCTION, str)
        assert isinstance(EXAMPLES_TEXT, str)
    
    def test_constants_are_not_empty_strings(self):
        """Test that constants are not just empty strings."""
        assert SYSTEM_INSTRUCTION.strip() != ""
        assert EXAMPLES_TEXT.strip() != ""
    
    def test_system_instruction_length_reasonable(self):
        """Test that SYSTEM_INSTRUCTION is substantial but not excessive."""
        # Should be at least 1000 characters (comprehensive)
        assert len(SYSTEM_INSTRUCTION) >= 1000
        # But not absurdly long (< 100k characters)
        assert len(SYSTEM_INSTRUCTION) < 100000
    
    def test_examples_length_reasonable(self):
        """Test that EXAMPLES_TEXT is substantial."""
        # Should be at least 100 characters
        assert len(EXAMPLES_TEXT) >= 100
        # But not absurdly long
        assert len(EXAMPLES_TEXT) < 50000

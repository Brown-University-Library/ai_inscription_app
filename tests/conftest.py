"""
Pytest fixtures and configuration for tests.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_file = tmp_path / "leiden_epidoc_config.json"
    config_data = {
        "api_key": "test-api-key-12345",
        "model": "claude-sonnet-4-20250514",
        "save_location": str(tmp_path)
    }
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    return config_file


@pytest.fixture
def sample_leiden_text():
    """Sample Leiden convention text for testing."""
    return """Εἶς θεὸ[ς μόνο-] 
ς ὁ βοηθ[ῶν] 
Γαδιωναν 
κ(αὶ) Ἰουλιανῷ"""


@pytest.fixture
def sample_epidoc_response():
    """Sample response with proper tags from the AI."""
    return """<analysis>
This is a test analysis of the inscription.
</analysis>

<notes>
Some notes about the translation.
</notes>

<final_translation>
<lb/>Εἶς θεὸ<supplied reason="lost">ς</supplied>
</final_translation>"""


@pytest.fixture
def sample_epidoc_response_no_tags():
    """Sample response without the expected tags."""
    return "<lb/>Εἶς θεὸ<supplied reason='lost'>ς</supplied>"


@pytest.fixture
def sample_file_content(tmp_path):
    """Create a sample text file with Leiden content."""
    file_path = tmp_path / "sample_inscription.txt"
    content = """[Marcus] Aurelius
v(iro) c(larissimo)
leg(ato) [[Imp(eratoris)]]"""
    file_path.write_text(content, encoding='utf-8')
    return file_path


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock()]
    mock_client.messages.create.return_value = mock_message
    return mock_client


@pytest.fixture
def mock_anthropic_response():
    """Mock response from Anthropic API."""
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = """<analysis>
Test analysis
</analysis>

<notes>
Test notes
</notes>

<final_translation>
<lb/>Test translation
</final_translation>"""
    mock_response.content = [mock_content]
    return mock_response


def create_mock_converter():
    """Create a mock converter for testing response parsing."""
    import re
    
    class MockConverter:
        """Mock converter that mimics LeidenToEpiDocConverter's _parse_response method."""
        ANALYSIS_PATTERN = re.compile(r'<analysis>(.*?)</analysis>', re.DOTALL | re.IGNORECASE)
        NOTES_PATTERN = re.compile(r'<notes>(.*?)</notes>', re.DOTALL | re.IGNORECASE)
        TRANSLATION_PATTERN = re.compile(r'<final_translation>(.*?)</final_translation>', re.DOTALL | re.IGNORECASE)
        
        def _parse_response(self, response_text: str) -> dict:
            result = {
                "full_text": response_text,
                "has_tags": False,
                "analysis": "",
                "notes": "",
                "final_translation": "",
                "error": None
            }
            
            analysis_match = self.ANALYSIS_PATTERN.search(response_text)
            notes_match = self.NOTES_PATTERN.search(response_text)
            translation_match = self.TRANSLATION_PATTERN.search(response_text)
            
            if analysis_match and notes_match and translation_match:
                result["has_tags"] = True
                result["analysis"] = analysis_match.group(1).strip()
                result["notes"] = notes_match.group(1).strip()
                result["final_translation"] = translation_match.group(1).strip()
            
            return result
    
    return MockConverter()

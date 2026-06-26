"""
test_braille.py

Unit tests for BrailleAgent.
Mocks the Gemini GenAI Client to verify:
1. Simple text translation.
2. Artwork description translation.
3. Long paragraph translation.
4. Empty input handling (fallback).
5. Invalid input / API error fallback.
"""

import os
import pytest
import unittest.mock as mock
from pydantic import ValidationError
from google.genai.errors import APIError

from src.agents.braille import (
    BrailleAgent,
    BrailleInput,
    BrailleOutput
)

@pytest.fixture
def mock_client():
    """Provides a mocked google-genai client."""
    client = mock.MagicMock()
    return client

@pytest.mark.asyncio
async def test_simple_text(mock_client):
    """Verifies translation of a simple text description."""
    agent = BrailleAgent(client=mock_client)

    mock_output = BrailleOutput(
        grade1_braille="A simple dog outline.",
        grade2_braille="A simple dog outline.",
        unicode_braille="⠠⠁ ⠎⠊⠍⠏⠇⠑ ⠙⠕⠛ ⠕⠥⠓⠇⠊⠝⠑⠲",
        plain_text="A simple dog outline.",
        character_count=22,
        translation_notes="Capital indicator applied at start.",
        confidence_score=0.95,
        metadata={"download_file_path": "outputs/braille_test_simple.txt"}
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    inp = BrailleInput(
        alt_text="A simple dog outline.",
        session_id="test_simple"
    )

    result = await agent.translate(inp)

    assert result.unicode_braille == "⠠⠁ ⠎⠊⠍⠏⠇⠑ ⠙⠕⠛ ⠕⠥⠓⠇⠊⠝⠑⠲"
    assert result.confidence_score == 0.95
    assert result.character_count == 22
    mock_client.models.generate_content.assert_called_once()

    # Clean up file generated during test if exists
    if result.metadata.get("download_file_path") and os.path.exists(result.metadata["download_file_path"]):
        os.remove(result.metadata["download_file_path"])

@pytest.mark.asyncio
async def test_artwork_description(mock_client):
    """Verifies translation of rich artwork descriptions including screen reader text and object list."""
    agent = BrailleAgent(client=mock_client)

    mock_output = BrailleOutput(
        grade1_braille="Starry Night painting has swirls and stars.",
        grade2_braille="Starry Night painting has swirls & stars.",
        unicode_braille="⠠⠎⠞⠁⠗⠗⠽ ⠠⠝⠊⠛⠓⠞...",
        plain_text="Starry Night painting description",
        character_count=42,
        translation_notes="Grade 2 contractions applied for 'and'.",
        confidence_score=0.98,
        metadata={"download_file_path": "outputs/braille_test_artwork.txt"}
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    inp = BrailleInput(
        screen_reader_description="The Starry Night by Vincent van Gogh with large swirling clouds.",
        alt_text="Starry Night artwork",
        object_list=["swirls", "stars", "clouds", "cypress tree"],
        session_id="test_artwork"
    )

    result = await agent.translate(inp)

    assert result.grade2_braille == "Starry Night painting has swirls & stars."
    assert "swirls & stars" in result.grade2_braille
    assert result.confidence_score == 0.98
    
    if result.metadata.get("download_file_path") and os.path.exists(result.metadata["download_file_path"]):
        os.remove(result.metadata["download_file_path"])

@pytest.mark.asyncio
async def test_long_paragraph(mock_client):
    """Verifies that the agent translates longer descriptions correctly."""
    agent = BrailleAgent(client=mock_client)

    long_description = (
        "This is an extremely long paragraph containing detailed descriptions of a tactile map. "
        "It includes a winding river flowing from the top-left to the bottom-right, "
        "a dense forest in the center represented by a cluster of trees, "
        "and a mountain range along the top border with high peaks."
    )

    mock_output = BrailleOutput(
        grade1_braille=long_description,
        grade2_braille="Contracted version of long paragraph.",
        unicode_braille="⠠⠞⠓⠊⠎ ⠊⠎...",
        plain_text=long_description,
        character_count=len(long_description),
        translation_notes="Long text processed without issue.",
        confidence_score=0.90,
        metadata={"download_file_path": "outputs/braille_test_long.txt"}
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    inp = BrailleInput(
        screen_reader_description=long_description,
        session_id="test_long"
    )

    result = await agent.translate(inp)

    assert result.plain_text == long_description
    assert result.confidence_score == 0.90
    
    if result.metadata.get("download_file_path") and os.path.exists(result.metadata["download_file_path"]):
        os.remove(result.metadata["download_file_path"])

@pytest.mark.asyncio
async def test_empty_input(mock_client):
    """Verifies that completely empty/invalid inputs are handled gracefully with fallback."""
    agent = BrailleAgent(client=mock_client)

    # Empty inputs should not call generate_content at all
    inp = BrailleInput(
        screen_reader_description="",
        easy_english_version="",
        child_friendly_version="",
        alt_text="",
        object_list=[]
    )

    result = await agent.translate(inp)

    assert result.confidence_score == 0.0
    assert "Missing inputs" in result.translation_notes
    assert result.unicode_braille == ""
    mock_client.models.generate_content.assert_not_called()

@pytest.mark.asyncio
async def test_invalid_input(mock_client):
    """Verifies that API errors trigger graceful fallback output."""
    agent = BrailleAgent(client=mock_client)

    # Mock API call to raise an exception
    mock_client.models.generate_content.side_effect = Exception("Model request limit exceeded.")

    inp = BrailleInput(
        screen_reader_description="Some text description.",
        session_id="test_invalid"
    )

    result = await agent.translate(inp)

    assert result.confidence_score == 0.0
    assert "Fallback triggered" in result.translation_notes
    assert "Model request limit" in result.translation_notes
    assert result.unicode_braille == ""

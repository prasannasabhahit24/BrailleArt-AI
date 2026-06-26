"""
test_art_knowledge.py

Unit tests for ArtKnowledgeAgent.
Mocks the Gemini GenAI Client to verify:
1. Famous painting recognition.
2. Unknown artwork handling (confidence low).
3. Modern digital artwork analysis.
4. Sketch analysis.
5. Invalid image bytes handling.
"""

import pytest
import io
import unittest.mock as mock
from PIL import Image
from pydantic import ValidationError
from google.genai.errors import APIError

from src.agents.art_knowledge import (
    ArtKnowledgeAgent,
    ArtKnowledgeInput,
    ArtKnowledgeOutput,
    SymbolismItem,
    SimilarArtwork
)

@pytest.fixture
def mock_client():
    """Provides a mocked google-genai client."""
    client = mock.MagicMock()
    return client

@pytest.fixture
def valid_image_bytes():
    """Generates a valid 1x1 PNG image as bytes to satisfy PIL loading checks."""
    img = Image.new('RGB', (1, 1), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

@pytest.mark.asyncio
async def test_famous_painting(mock_client, valid_image_bytes):
    """Verifies that the agent correctly parses a famous painting response."""
    agent = ArtKnowledgeAgent(client=mock_client)
    
    mock_output = ArtKnowledgeOutput(
        artwork_title="The Starry Night",
        artist="Vincent van Gogh",
        art_movement="Post-Impressionism",
        medium="Oil on canvas",
        estimated_year="1889",
        symbolism=[
            SymbolismItem(element="Cypress tree", meaning="Mourning and eternity", reasoning="Links earth and sky.")
        ],
        historical_context="Painted from his asylum room window.",
        cultural_significance="Icon of modern art.",
        similar_artworks=[
            SimilarArtwork(title="The Scream", artist="Edvard Munch", comparison="Expressionist mood.")
        ],
        confidence_score=0.98,
        reasoning="Highly distinctive brushstrokes and colors match Van Gogh's Starry Night."
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_ok = True
    mock_client.models.generate_content.return_value = mock_response

    input_data = ArtKnowledgeInput(image_bytes=valid_image_bytes)
    result = await agent.identify_artwork(input_data)

    assert result.artwork_title == "The Starry Night"
    assert result.artist == "Vincent van Gogh"
    assert result.confidence_score == 0.98
    assert len(result.symbolism) == 1
    mock_client.models.generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_unknown_artwork(mock_client, valid_image_bytes):
    """Verifies that low-confidence results are translated to 'unknown artwork'."""
    agent = ArtKnowledgeAgent(client=mock_client)
    
    mock_output = ArtKnowledgeOutput(
        artwork_title="unknown artwork",
        artist="unknown artist",
        art_movement="unknown",
        medium="oil sketch",
        estimated_year="unknown",
        symbolism=[],
        historical_context="Unknown historical details.",
        cultural_significance="No significant cultural records.",
        similar_artworks=[],
        confidence_score=0.35,
        reasoning="Image is a generic portrait without recognizable fine art features."
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    input_data = ArtKnowledgeInput(image_bytes=valid_image_bytes)
    result = await agent.identify_artwork(input_data)

    assert result.artwork_title == "unknown artwork"
    assert result.artist == "unknown artist"
    assert result.confidence_score < 0.70
    assert "generic portrait" in result.reasoning

@pytest.mark.asyncio
async def test_modern_digital_artwork(mock_client, valid_image_bytes):
    """Verifies handling of modern digital illustration uploads."""
    agent = ArtKnowledgeAgent(client=mock_client)
    
    mock_output = ArtKnowledgeOutput(
        artwork_title="unknown artwork",
        artist="unknown artist",
        art_movement="Modern Digital Art",
        medium="Digital painting",
        estimated_year="c. 2020s",
        symbolism=[],
        historical_context="Modern creation.",
        cultural_significance="None.",
        similar_artworks=[],
        confidence_score=0.20,
        reasoning="Digital graphics character design. Not recognized as a historical artwork."
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    input_data = ArtKnowledgeInput(image_bytes=valid_image_bytes)
    result = await agent.identify_artwork(input_data)

    assert result.artwork_title == "unknown artwork"
    assert result.medium == "Digital painting"
    assert "Digital graphics" in result.reasoning

@pytest.mark.asyncio
async def test_sketch(mock_client, valid_image_bytes):
    """Verifies sketch image handling."""
    agent = ArtKnowledgeAgent(client=mock_client)
    
    mock_output = ArtKnowledgeOutput(
        artwork_title="unknown artwork",
        artist="unknown artist",
        art_movement="Sketching",
        medium="Pencil on paper",
        estimated_year="unknown",
        symbolism=[],
        historical_context="Freehand pencil sketch.",
        cultural_significance="None.",
        similar_artworks=[],
        confidence_score=0.15,
        reasoning="Pencil line drawing, likely user-created doodle."
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    input_data = ArtKnowledgeInput(image_bytes=valid_image_bytes)
    result = await agent.identify_artwork(input_data)

    assert result.artwork_title == "unknown artwork"
    assert "doodle" in result.reasoning
    assert result.confidence_score == 0.15

@pytest.mark.asyncio
async def test_invalid_image(mock_client):
    """Verifies that passing corrupted or invalid bytes triggers fallback values gracefully."""
    agent = ArtKnowledgeAgent(client=mock_client)

    # Note: Invalid bytes will fail PIL.Image.open and raise OSError, triggering fallback.
    input_data = ArtKnowledgeInput(image_bytes=b"corrupted_header_data")
    result = await agent.identify_artwork(input_data)

    assert result.artwork_title == "unknown artwork"
    assert result.artist == "unknown artist"
    assert result.confidence_score == 0.0
    assert "Processing Failure" in result.reasoning
    mock_client.models.generate_content.assert_not_called()

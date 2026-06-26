"""
test_tactile.py

Unit tests for TactileAgent.
Mocks the Gemini GenAI Client to verify:
1. Landscape painting layout.
2. Portrait layout.
3. Abstract artwork layout.
4. Artwork with text layout.
5. Invalid image/error fallback behavior.
"""

import os
import pytest
import unittest.mock as mock
from pydantic import ValidationError
from google.genai.errors import APIError

from src.agents.tactile import (
    TactileAgent,
    TactileInput,
    TactileOutput
)

@pytest.fixture
def mock_client():
    """Provides a mocked google-genai client."""
    client = mock.MagicMock()
    return client

@pytest.mark.asyncio
async def test_landscape_painting(mock_client):
    """Verifies tactile layout generation for a landscape painting."""
    agent = TactileAgent(client=mock_client)

    mock_output = TactileOutput(
        simplified_svg='<svg><path d="M 0,50 Q 50,20 100,50" /></svg>',
        raised_line_layout="Raised lines for mountains and sun.",
        object_boundary_map={"mountains": [0, 30, 100, 40], "sun": [40, 10, 20, 20]},
        relative_spatial_positions={"sun": "above mountains", "mountains": "bottom half"},
        braille_overlay_coordinates={"sun_label": [50, 20], "mountain_label": [50, 60]},
        embosser_ready_svg='<svg><path d="M 0,50 Q 50,20 100,50" stroke-dasharray="2,2" /></svg>',
        metadata={"simplified_svg_path": "outputs/tactile_simplified_landscape.svg"},
        confidence_score=0.95
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    inp = TactileInput(
        vision_output={"type": "landscape", "elements": ["mountains", "sun"]},
        accessibility_output={"alt_text": "A landscape with mountains and sun."},
        session_id="test_landscape"
    )

    result = await agent.generate_tactile_layout(inp)

    assert "<svg>" in result.simplified_svg
    assert "mountains" in result.object_boundary_map
    assert result.confidence_score == 0.95
    mock_client.models.generate_content.assert_called_once()

    # Clean up generated files if they exist
    for key in ["simplified_svg_path", "embosser_ready_svg_path"]:
        path = result.metadata.get(key)
        if path and os.path.exists(path):
            os.remove(path)

@pytest.mark.asyncio
async def test_portrait(mock_client):
    """Verifies tactile layout generation for a portrait artwork."""
    agent = TactileAgent(client=mock_client)

    mock_output = TactileOutput(
        simplified_svg='<svg><circle cx="50" cy="50" r="30" /></svg>',
        raised_line_layout="Raised circle for face contour.",
        object_boundary_map={"face": [20, 20, 60, 60]},
        relative_spatial_positions={"face": "center"},
        braille_overlay_coordinates={"face_label": [50, 50]},
        embosser_ready_svg='<svg><circle cx="50" cy="50" r="30" /></svg>',
        metadata={"simplified_svg_path": "outputs/tactile_simplified_portrait.svg"},
        confidence_score=0.92
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    inp = TactileInput(
        vision_output={"type": "portrait", "elements": ["face", "eyes"]},
        accessibility_output={"alt_text": "A portrait of a woman."},
        session_id="test_portrait"
    )

    result = await agent.generate_tactile_layout(inp)

    assert "face" in result.object_boundary_map
    assert result.confidence_score == 0.92

    for key in ["simplified_svg_path", "embosser_ready_svg_path"]:
        path = result.metadata.get(key)
        if path and os.path.exists(path):
            os.remove(path)

@pytest.mark.asyncio
async def test_abstract_artwork(mock_client):
    """Verifies tactile layout generation for abstract geometric shapes."""
    agent = TactileAgent(client=mock_client)

    mock_output = TactileOutput(
        simplified_svg='<svg><rect x="10" y="10" width="80" height="80" /></svg>',
        raised_line_layout="Raised lines for square block boundaries.",
        object_boundary_map={"square": [10, 10, 80, 80]},
        relative_spatial_positions={"square": "covers entire canvas"},
        braille_overlay_coordinates={"square_label": [50, 50]},
        embosser_ready_svg='<svg><rect x="10" y="10" width="80" height="80" /></svg>',
        metadata={"simplified_svg_path": "outputs/tactile_simplified_abstract.svg"},
        confidence_score=0.88
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    inp = TactileInput(
        vision_output={"type": "abstract", "elements": ["square"]},
        accessibility_output={"alt_text": "An abstract composition with a large square."},
        session_id="test_abstract"
    )

    result = await agent.generate_tactile_layout(inp)

    assert "square" in result.object_boundary_map
    assert result.confidence_score == 0.88

    for key in ["simplified_svg_path", "embosser_ready_svg_path"]:
        path = result.metadata.get(key)
        if path and os.path.exists(path):
            os.remove(path)

@pytest.mark.asyncio
async def test_artwork_with_text(mock_client):
    """Verifies tactile layout generation for artwork containing OCR-detected text labels."""
    agent = TactileAgent(client=mock_client)

    mock_output = TactileOutput(
        simplified_svg='<svg><text x="10" y="30">LOGO</text></svg>',
        raised_line_layout="Raised text block outline.",
        object_boundary_map={"text_label": [10, 20, 40, 15]},
        relative_spatial_positions={"text_label": "top-left"},
        braille_overlay_coordinates={"text_label_braille": [10, 30]},
        embosser_ready_svg='<svg><text x="10" y="30">LOGO</text></svg>',
        metadata={"simplified_svg_path": "outputs/tactile_simplified_text.svg"},
        confidence_score=0.90
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    inp = TactileInput(
        vision_output={"type": "graphic"},
        ocr_output={"combined_text": "LOGO"},
        braille_output={"unicode_braille": "⠠⠇⠕⠛⠕"},
        session_id="test_text"
    )

    result = await agent.generate_tactile_layout(inp)

    assert "text_label" in result.object_boundary_map
    assert result.confidence_score == 0.90

    for key in ["simplified_svg_path", "embosser_ready_svg_path"]:
        path = result.metadata.get(key)
        if path and os.path.exists(path):
            os.remove(path)

@pytest.mark.asyncio
async def test_invalid_image(mock_client):
    """Verifies that API/internal exceptions trigger fallback outputs gracefully."""
    agent = TactileAgent(client=mock_client)

    # Force an API error on call
    mock_client.models.generate_content.side_effect = Exception("API Error: Gemini rate limit reached.")

    inp = TactileInput(
        vision_output={"elements": []},
        session_id="test_invalid"
    )

    result = await agent.generate_tactile_layout(inp)

    # Should trigger fallback output gracefully
    assert "<svg" in result.simplified_svg
    assert result.confidence_score == 0.0
    assert result.object_boundary_map == {}
    assert result.metadata["fallback_active"] is True

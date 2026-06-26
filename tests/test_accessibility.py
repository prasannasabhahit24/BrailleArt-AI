"""
test_accessibility.py

Unit tests for AccessibilityAgent.
Mocks the Gemini GenAI Client to verify:
1. Famous artwork accessibility packaging.
2. Artwork containing text description.
3. Abstract artwork description.
4. Child mode description.
5. Error/invalid input fallback triggers.
"""

import pytest
import unittest.mock as mock
from pydantic import ValidationError

from src.agents.accessibility import (
    AccessibilityAgent,
    AccessibilityInput,
    AccessibilityOutput,
    AccessibilityScoreDetails
)

@pytest.fixture
def mock_client():
    """Provides a mocked google-genai client."""
    client = mock.MagicMock()
    return client

@pytest.mark.asyncio
async def test_famous_artwork(mock_client):
    """Verifies that the agent correctly packages accessibility content for famous art."""
    agent = AccessibilityAgent(client=mock_client)
    
    mock_output = AccessibilityOutput(
        screen_reader_description="The image is a painting of a woman, Mona Lisa, seated, smiling slightly.",
        easy_english_version="This is a famous painting of a woman smiling.",
        child_friendly_version="Meet the Mona Lisa! She has a soft smile and sits in front of distant hills.",
        audio_narration_script="Start tracing at the top for her hair, then slide down to her hands.",
        alt_text="Mona Lisa painting by Leonardo da Vinci",
        object_list=["woman", "hills", "hands"],
        spatial_layout_description="Central portrait layout with landscape background.",
        accessibility_score=AccessibilityScoreDetails(
            completeness=0.95,
            readability=0.90,
            usefulness=0.95,
            screen_reader_compatibility=0.98,
            overall_score=0.94
        ),
        suggested_improvements=["None required."],
        confidence_score=0.98,
        reasoning="Well-known artwork allows highly complete and compatible formatting."
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    inp = AccessibilityInput(
        text_context="Mona Lisa",
        braille_output="⠀⠀⠀⠠⠓⠑⠇⠇⠕⠀⠀⠀",
        vision_output={"elements": [{"label": "woman", "bounding_box": [0.1, 0.2, 0.9, 0.8]}]},
        art_knowledge_output={"artwork_title": "Mona Lisa", "artist": "Leonardo da Vinci"}
    )

    result = await agent.generate_accessibility_pack(inp)

    assert result.alt_text == "Mona Lisa painting by Leonardo da Vinci"
    assert result.accessibility_score.overall_score == 0.94
    assert "hands" in result.object_list
    mock_client.models.generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_artwork_containing_text(mock_client):
    """Verifies that OCR text signals are successfully integrated into descriptions."""
    agent = AccessibilityAgent(client=mock_client)
    
    mock_output = AccessibilityOutput(
        screen_reader_description="Diagram titled 'FLOW CHART' with three arrows.",
        easy_english_version="A diagram that shows a flow chart.",
        child_friendly_version="This is a path showing how ideas flow! It says 'FLOW CHART' at the top.",
        audio_narration_script="Read the title at the top, then follow the arrows down.",
        alt_text="Flow chart diagram containing text",
        object_list=["title label", "arrow vectors"],
        spatial_layout_description="Flow chart box at top, arrows pointing down to columns.",
        accessibility_score=AccessibilityScoreDetails(
            completeness=0.92,
            readability=0.88,
            usefulness=0.90,
            screen_reader_compatibility=0.95,
            overall_score=0.91
        ),
        suggested_improvements=["Highlight arrows with higher contrast dots."],
        confidence_score=0.94,
        reasoning="Visible text makes label descriptions straightforward and useful."
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    inp = AccessibilityInput(
        text_context="Diagram with text",
        ocr_output={"combined_text": "FLOW CHART"}
    )

    result = await agent.generate_accessibility_pack(inp)

    assert result.alt_text == "Flow chart diagram containing text"
    assert "FLOW CHART" in result.child_friendly_version
    assert result.confidence_score == 0.94

@pytest.mark.asyncio
async def test_abstract_artwork(mock_client):
    """Verifies description layout for abstract geometric patterns."""
    agent = AccessibilityAgent(client=mock_client)
    
    mock_output = AccessibilityOutput(
        screen_reader_description="Abstract layout of concentric circles and intersecting lines.",
        easy_english_version="A pattern of circles inside other circles with crossing lines.",
        child_friendly_version="Lots of round target circles with lines going through them!",
        audio_narration_script="Trace the circle loops starting from the center outward.",
        alt_text="Abstract pattern of concentric circles",
        object_list=["circles", "lines"],
        spatial_layout_description="Concentric circles centered in the frame.",
        accessibility_score=AccessibilityScoreDetails(
            completeness=0.85,
            readability=0.85,
            usefulness=0.80,
            screen_reader_compatibility=0.90,
            overall_score=0.85
        ),
        suggested_improvements=["Simplify overlapping lines to improve tactile scanning."],
        confidence_score=0.88,
        reasoning="Abstract layouts require spatial geometric categorization instead of literal labels."
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    inp = AccessibilityInput(
        text_context="Abstract circles"
    )

    result = await agent.generate_accessibility_pack(inp)

    assert result.alt_text == "Abstract pattern of concentric circles"
    assert "concentric circles" in result.spatial_layout_description.lower()

@pytest.mark.asyncio
async def test_child_mode(mock_client):
    """Verifies child-friendly description attributes."""
    agent = AccessibilityAgent(client=mock_client)
    
    mock_output = AccessibilityOutput(
        screen_reader_description="A cartoon drawing of a puppy.",
        easy_english_version="This is a drawing of a small dog.",
        child_friendly_version="Say hello to a cute little puppy! He has floppy ears and a happy tail.",
        audio_narration_script="Trace his floppy ears at the top left and right.",
        alt_text="Cute puppy illustration",
        object_list=["puppy", "ears", "tail"],
        spatial_layout_description="Centered puppy silhouette.",
        accessibility_score=AccessibilityScoreDetails(
            completeness=0.90,
            readability=0.95,
            usefulness=0.90,
            screen_reader_compatibility=0.95,
            overall_score=0.92
        ),
        suggested_improvements=[],
        confidence_score=0.96,
        reasoning="Child mode requested, prioritizing playful descriptors."
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    inp = AccessibilityInput(
        text_context="Draw a puppy for a kid",
        user_prompt="kid mode description"
    )

    result = await agent.generate_accessibility_pack(inp)

    assert "floppy ears" in result.child_friendly_version
    assert result.alt_text == "Cute puppy illustration"

@pytest.mark.asyncio
async def test_invalid_image(mock_client):
    """Verifies that API/internal exceptions trigger fallback outputs gracefully."""
    agent = AccessibilityAgent(client=mock_client)

    # Force an API error on call
    mock_client.models.generate_content.side_effect = Exception("API Error: Gemini model limit exceeded")

    inp = AccessibilityInput(
        text_context="Joyous painting",
        braille_output="⠀⠀"
    )

    result = await agent.generate_accessibility_pack(inp)

    # Should trigger fallback output gracefully
    assert result.alt_text == "uncertain alt text"
    assert result.accessibility_score.overall_score == 0.0
    assert "API Error" in result.reasoning

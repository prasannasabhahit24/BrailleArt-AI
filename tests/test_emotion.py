"""
test_emotion.py

Unit tests for EmotionAgent.
Mocks the Gemini GenAI Client to verify:
1. Joyful painting emotion parsing.
2. Sad artwork emotion parsing.
3. Abstract painting emotion parsing.
4. Unknown/low-confidence artwork handling.
5. Error/invalid input fallback trigger.
"""

import pytest
import unittest.mock as mock
from pydantic import ValidationError
from google.genai.errors import APIError

from src.agents.emotion import (
    EmotionAgent,
    EmotionInput,
    EmotionOutput
)

@pytest.fixture
def mock_client():
    """Provides a mocked google-genai client."""
    client = mock.MagicMock()
    return client

@pytest.mark.asyncio
async def test_joyful_painting(mock_client):
    """Verifies parsing of joyful or celebratory artwork signals."""
    agent = EmotionAgent(client=mock_client)
    
    mock_output = EmotionOutput(
        dominant_emotion="joy",
        secondary_emotions=["warmth", "optimism"],
        atmosphere="celebratory and vibrant",
        symbolism="Sunlight and blooming fields symbolize rebirth and happiness.",
        storytelling="Characters are dancing in a circle, depicting communal bliss.",
        artistic_intention="To evoke a sense of cheerfulness and connect the viewer to nature's cycles.",
        emotional_summary="Vibrant yellows and active composition convey deep joy.",
        confidence_score=0.95,
        reasoning="Yellow color palette, laughing figures, and the user prompt 'happy dance' point directly to joy."
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    inp = EmotionInput(
        user_prompt="Render this happy summer dance painting.",
        visual_description="People dancing outdoors under bright sun.",
        vision_output={"color_analysis": {"dominant_colors": ["yellow", "green"], "contrast_level": "high"}},
        ocr_output={"combined_text": "Summer Festival"},
        art_knowledge_output={"art_movement": "Impressionism", "artwork_title": "Summer Dance"}
    )

    result = await agent.analyze_emotion(inp)

    assert result.dominant_emotion == "joy"
    assert "warmth" in result.secondary_emotions
    assert result.confidence_score == 0.95
    mock_client.models.generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_sad_artwork(mock_client):
    """Verifies parsing of sorrowful or melancholic artwork signals."""
    agent = EmotionAgent(client=mock_client)
    
    mock_output = EmotionOutput(
        dominant_emotion="sorrow",
        secondary_emotions=["grief", "isolation"],
        atmosphere="somber and gloomy",
        symbolism="Rain and dark blue tones depict weeping and isolation.",
        storytelling="A single slouched figure stands alone, portraying despair.",
        artistic_intention="To prompt reflection on loneliness and sorrow.",
        emotional_summary="Monochromatic blues and descending lines elicit melancholy.",
        confidence_score=0.92,
        reasoning="Blue hues, a slouched figure, and the prompt 'loneliness' match sorrow."
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    inp = EmotionInput(
        user_prompt="Translate this sad and lonely rain scene.",
        visual_description="One person slouched in dark rain.",
        vision_output={"color_analysis": {"dominant_colors": ["blue", "dark gray"], "contrast_level": "low"}},
        ocr_output=None,
        art_knowledge_output=None
    )

    result = await agent.analyze_emotion(inp)

    assert result.dominant_emotion == "sorrow"
    assert "grief" in result.secondary_emotions
    assert result.confidence_score == 0.92

@pytest.mark.asyncio
async def test_abstract_painting(mock_client):
    """Verifies emotional mapping for complex or chaotic abstract artworks."""
    agent = EmotionAgent(client=mock_client)
    
    mock_output = EmotionOutput(
        dominant_emotion="excitement",
        secondary_emotions=["confusion", "tension"],
        atmosphere="energetic and dynamic",
        symbolism="Sharp red angles suggest conflict, while curved splatters convey release.",
        storytelling="Non-representational vectors collide in chaotic motion.",
        artistic_intention="To disrupt traditional spatial balance and trigger raw visceral excitement.",
        emotional_summary="Sharp shapes and saturated reds create dynamic tension.",
        confidence_score=0.88,
        reasoning="High contrast, sharp angles, and user description of 'clash of shapes' suggest excitement."
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    inp = EmotionInput(
        user_prompt="I want abstract red lines colliding.",
        visual_description="Chaotic red and black geometric vectors.",
        vision_output={"color_analysis": {"dominant_colors": ["red", "black"], "contrast_level": "high"}},
        ocr_output=None,
        art_knowledge_output=None
    )

    result = await agent.analyze_emotion(inp)

    assert result.dominant_emotion == "excitement"
    assert "tension" in result.secondary_emotions
    assert result.confidence_score == 0.88

@pytest.mark.asyncio
async def test_unknown_artwork(mock_client):
    """Verifies that low-confidence/ambiguous contexts map to uncertainty outputs."""
    agent = EmotionAgent(client=mock_client)
    
    mock_output = EmotionOutput(
        dominant_emotion="uncertain dominant emotion",
        secondary_emotions=[],
        atmosphere="uncertain atmosphere",
        symbolism="No clear symbolic motifs detected.",
        storytelling="Ambiguous spatial layouts provide no clear story.",
        artistic_intention="Unclear due to lacking contextual signals.",
        emotional_summary="Ambiguous cues prevent a confident emotional profile.",
        confidence_score=0.45,
        reasoning="The inputs consist only of a generic blank grid without outline details."
    )

    mock_response = mock.MagicMock()
    mock_response.text = mock_output.model_dump_json()
    mock_client.models.generate_content.return_value = mock_response

    inp = EmotionInput(
        user_prompt="Render this empty grid shape.",
        visual_description="Blank canvas background.",
        vision_output=None,
        ocr_output=None,
        art_knowledge_output=None
    )

    result = await agent.analyze_emotion(inp)

    assert result.dominant_emotion == "uncertain dominant emotion"
    assert result.atmosphere == "uncertain atmosphere"
    assert result.confidence_score < 0.70

@pytest.mark.asyncio
async def test_invalid_image(mock_client):
    """Verifies that API/internal exceptions trigger fallback outputs gracefully."""
    agent = EmotionAgent(client=mock_client)

    # Force an API error on call
    mock_client.models.generate_content.side_effect = Exception("API Error: Gemini model limit exceeded")

    inp = EmotionInput(
        user_prompt="Joyous painting",
        visual_description="Bright colors"
    )

    result = await agent.analyze_emotion(inp)

    # Should trigger fallback output gracefully
    assert result.dominant_emotion == "uncertain dominant emotion"
    assert result.confidence_score == 0.0
    assert "API Error" in result.reasoning

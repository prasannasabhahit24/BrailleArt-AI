"""
emotion.py

Emotion Agent for BrailleArt AI.
Responsibility:
Analyzes the mood, atmosphere, tone, color psychology, and storytelling of an artwork.
Combines information from the user prompt, Vision Agent layout summaries, OCR text segments,
and Art Knowledge history to formulate a unified emotional profile using Gemini 2.5 Flash.
Provides low-confidence uncertainty indicators if the context is ambiguous.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv

# Initialize logging
logger = logging.getLogger("brailleart_ai.emotion")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Load environment variables
load_dotenv()

class EmotionInput(BaseModel):
    """Input payload combining multiple agent outputs for emotional inference."""
    user_prompt: str = Field(..., description="The user's original query or context prompt.")
    visual_description: Optional[str] = Field(default=None, description="Spatial and visual layout summary (from orchestrator).")
    vision_output: Optional[Dict[str, Any]] = Field(default=None, description="Detailed Vision Agent output dictionary.")
    ocr_output: Optional[Dict[str, Any]] = Field(default=None, description="OCR Agent text analysis dictionary.")
    art_knowledge_output: Optional[Dict[str, Any]] = Field(default=None, description="Art Knowledge Agent context dossier.")

class EmotionOutput(BaseModel):
    """Structured report profiling the emotional properties of the artwork."""
    dominant_emotion: str = Field(..., description="The main mood or emotional quality detected. Set to exactly 'uncertain dominant emotion' if confidence is low.")
    secondary_emotions: List[str] = Field(..., description="Other minor or complex emotions detected (e.g. anxiety, serenity).")
    atmosphere: str = Field(..., description="The ambiance/atmosphere of the scene (e.g. calm, chaotic, tense, joyful).")
    symbolism: str = Field(..., description="Explanation of how visual symbolism contributes to the emotion.")
    storytelling: str = Field(..., description="Analysis of the visual storytelling and narrative emotional cues.")
    artistic_intention: str = Field(..., description="The likely intention of the artist (what they wanted the viewer to feel).")
    emotional_summary: str = Field(..., description="A concise narrative summary of the emotional landscape.")
    confidence_score: float = Field(..., description="Confidence score in this emotional evaluation, from 0.0 to 1.0.")
    reasoning: str = Field(..., description="Detailed explanation of WHY each conclusion was reached, quoting colors, layout, text, or context.")

class EmotionAgent:
    """
    EmotionAgent class utilizing Gemini 2.5 Flash to synthesize emotional intelligence 
    from multiple sub-agent signals.
    """

    def __init__(self, client: Optional[genai.Client] = None):
        """
        Initializes the EmotionAgent with an optional pre-configured Gemini client.
        If no client is provided, checks environment variables and instantiates a new client.
        """
        self._client = client
        self.system_prompt = (
            "You are the Emotion Agent for BrailleArt AI.\n"
            "Your task is to analyze and synthesize the emotional tone of an artwork.\n\n"
            "Combine signals from:\n"
            "- User Prompt\n"
            "- Vision Agent layout descriptions (composition, colors, contrast, shapes)\n"
            "- OCR Agent text labels\n"
            "- Art Knowledge Agent context (artist intent, movement theme)\n\n"
            "You must infer dominant/secondary emotions, atmosphere, symbolism, visual storytelling, "
            "color psychology, composition influence, and artistic intention.\n\n"
            "Rules for uncertainty:\n"
            "1. If confidence in the emotional tone is low (confidence < 0.70) due to ambiguous, "
            "corrupted, or empty signals, set 'dominant_emotion' to exactly 'uncertain dominant emotion' "
            "and describe your uncertainty in the reasoning field. Never invent facts.\n"
            "2. For each field, explain WHY you reached the conclusion, drawing links to the inputs."
        )

    @property
    def client(self) -> genai.Client:
        """Lazily instantiates the GenAI Client when needed."""
        if self._client is None:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY is not defined in the environment. Client calls will fail.")
            self._client = genai.Client()
        return self._client

    async def analyze_emotion(self, input_data: EmotionInput) -> EmotionOutput:
        """
        Synthesizes multi-agent signals to evaluate emotional tone asynchronously.
        Provides a static fallback model if model calls or serialization fails.
        
        Args:
            input_data (EmotionInput): Combined inputs from user prompt, vision, OCR, and history.
            
        Returns:
            EmotionOutput: Structured emotional dossier.
        """
        logger.info(f"Received request for emotional analysis (user_prompt: '{input_data.user_prompt}').")

        try:
            # Build text-based payload representing all available inputs
            contents = [
                f"User Prompt: {input_data.user_prompt}\n"
                f"Visual Description: {input_data.visual_description}\n"
                f"Vision Agent Output: {input_data.vision_output}\n"
                f"OCR Agent Output: {input_data.ocr_output}\n"
                f"Art Knowledge Agent Output: {input_data.art_knowledge_output}"
            ]

            # Invoke Gemini 2.5 Flash
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=EmotionOutput,
                    system_instruction=self.system_prompt,
                    temperature=0.1
                )
            )

            if response.text:
                output = EmotionOutput.model_validate_json(response.text)
                logger.info(f"Emotional analysis generated. Dominant: {output.dominant_emotion} (Confidence: {output.confidence_score}).")
                return output
            else:
                raise ValueError("Empty response text returned by the model.")

        except APIError as api_err:
            logger.error(f"Gemini API call failed during emotional analysis: {api_err}. Using fallback.", exc_info=True)
            return self._get_fallback_output(f"API Error: {str(api_err)}")
        except Exception as exc:
            logger.error(f"Failed to process inputs or parse response: {exc}. Using fallback.", exc_info=True)
            return self._get_fallback_output(f"Processing Failure: {str(exc)}")

    def _get_fallback_output(self, error_message: str) -> EmotionOutput:
        """
        Builds a safe fallback emotional profile when model calls cannot execute.
        """
        return EmotionOutput(
            dominant_emotion="uncertain dominant emotion",
            secondary_emotions=[],
            atmosphere="unknown atmosphere",
            symbolism="Unknown symbolism.",
            storytelling="Unknown storytelling.",
            artistic_intention="Unknown intention.",
            emotional_summary="Uncertain emotional tone due to system processing error.",
            confidence_score=0.0,
            reasoning=f"Fallback profile triggered due to execution error: {error_message}"
        )

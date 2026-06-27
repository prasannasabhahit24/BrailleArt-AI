"""
accessibility.py

Accessibility Agent for BrailleArt AI.
Responsibility:
Synthesizes Vision, OCR, Art Knowledge, and Emotion Agent signals to compile 
a complete Accessibility Package.
Includes screen-reader text, Easy English profiles, child descriptions, audio guides, 
concise alt text, spatial layout descriptions, object lists, and accessibility scores.
If confidence is low, details uncertainty rather than inventing facts.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv

from ..utils.helpers import setup_logger

# Initialize logging
logger = setup_logger("brailleart_ai.accessibility")

# Load environment variables
load_dotenv()

class AccessibilityInput(BaseModel):
    """Input payload containing drawing layouts and other agent signals."""
    user_prompt: Optional[str] = Field(default="", description="The user's original query or prompt.")
    braille_output: Optional[str] = Field(default="", description="The rendered Braille unicode artwork (from orchestrator).")
    text_context: Optional[str] = Field(default="", description="The description or context string (from orchestrator).")
    has_audio_enabled: Optional[bool] = Field(default=True, description="Flag indicating if audio narration script is needed.")
    
    # Combined outputs from other agents
    vision_output: Optional[Dict[str, Any]] = Field(default=None, description="Detailed Vision Agent output.")
    ocr_output: Optional[Dict[str, Any]] = Field(default=None, description="OCR Agent text output.")
    art_knowledge_output: Optional[Dict[str, Any]] = Field(default=None, description="Art Knowledge Agent context.")
    emotion_output: Optional[Dict[str, Any]] = Field(default=None, description="Emotion Agent mood analysis.")

class AccessibilityScoreDetails(BaseModel):
    """Grading indicators for accessibility quality assessment."""
    completeness: float = Field(..., description="Fidelity score of description detail (0.0 to 1.0).")
    readability: float = Field(..., description="Cognitive ease of reading (0.0 to 1.0).")
    usefulness: float = Field(..., description="General utility score for visual replacement (0.0 to 1.0).")
    screen_reader_compatibility: float = Field(..., description="Formatting check for JAWS/NVDA screen readers (0.0 to 1.0).")
    overall_score: float = Field(..., description="Weighted global score (0.0 to 1.0).")

class AccessibilityOutput(BaseModel):
    """Comprehensive accessibility package returned by the agent."""
    screen_reader_description: str = Field(..., description="Detailed, structure-by-structure text description optimized for screen readers.")
    easy_english_version: str = Field(..., description="Simplified English version written with short sentences and basic grammar.")
    child_friendly_version: str = Field(..., description="Playful, descriptive version suited for children or young learners.")
    audio_narration_script: str = Field(..., description="Spoken-word narration script describing how to explore the tactile dots.")
    alt_text: str = Field(..., description="Concise alternative text for web frameworks. Set to exactly 'uncertain alt text' if confidence is low.")
    object_list: List[str] = Field(..., description="List of visual objects or text blocks identified.")
    spatial_layout_description: str = Field(..., description="Explanation of coordinates, positioning, scale, and layout in the image grid.")
    accessibility_score: AccessibilityScoreDetails = Field(..., description="Quality scores evaluating completeness, readability, utility, and compatibility.")
    suggested_improvements: List[str] = Field(..., description="Recommendations to enhance description or drawing accessibility.")
    confidence_score: float = Field(..., description="Confidence score in the accessibility pack generation, from 0.0 to 1.0.")
    reasoning: str = Field(..., description="Explanation of why this description layout was selected and how scores were evaluated.")

class AccessibilityAgent:
    """
    AccessibilityAgent class utilizing Gemini 2.5 Flash to synthesize visual/tactile descriptions
    and score formatting completeness.
    """

    def __init__(self, client: Optional[genai.Client] = None):
        """
        Initializes the AccessibilityAgent with an optional pre-configured Gemini client.
        If no client is provided, checks environment variables and instantiates a new client.
        """
        self._client = client
        self.system_prompt = (
            "You are the Accessibility Agent for BrailleArt AI.\n"
            "Your task is to review all available agent outputs (Vision, OCR, Art, Emotion, User Prompt) "
            "and synthesize a comprehensive, multi-layered Accessibility Package.\n\n"
            "Generate:\n"
            "1. Detailed screen-reader spatial explanations.\n"
            "2. Easy English translations.\n"
            "3. Child-friendly, engaging descriptions.\n"
            "4. Step-by-step audio narration guidance scripts.\n"
            "5. Short, precise alt text.\n"
            "6. Object catalog and layout positioning coordinates.\n"
            "7. Grading score details (evaluating completeness, readability, usefulness, screen reader compatibility).\n"
            "8. Suggested tactile improvements.\n\n"
            "Rules for low-confidence:\n"
            "1. If confidence in the visual cues or description is low (confidence < 0.70) due to empty, "
            "corrupted, or mismatched inputs, set 'alt_text' to exactly 'uncertain alt text'. "
            "Record uncertainty explanations in reasoning and set scores to zero or default levels. Never invent facts."
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

    async def generate_accessibility_pack(self, input_data: AccessibilityInput) -> AccessibilityOutput:
        """
        Generates accessibility descriptions and evaluates quality scores asynchronously.
        Provides a static fallback model if model calls or serialization fails.
        
        Args:
            input_data (AccessibilityInput): Combined inputs from drawing outputs and sub-agent reports.
            
        Returns:
            AccessibilityOutput: Unified accessibility package.
        """
        prompt_ref = input_data.text_context or input_data.user_prompt or "unknown query"
        logger.info(f"Received request for accessibility profiling (context prompt: '{prompt_ref}').")

        try:
            # Package all context parameters for model evaluation
            contents = [
                f"Context Prompt: {prompt_ref}\n"
                f"Braille Drawing: {input_data.braille_output}\n"
                f"Vision Agent Output: {input_data.vision_output}\n"
                f"OCR Agent Output: {input_data.ocr_output}\n"
                f"Art Knowledge Agent Output: {input_data.art_knowledge_output}\n"
                f"Emotion Agent Output: {input_data.emotion_output}\n"
                f"Has Audio Enabled: {input_data.has_audio_enabled}"
            ]

            # Invoke Gemini 2.5 Flash
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AccessibilityOutput,
                    system_instruction=self.system_prompt,
                    temperature=0.1
                )
            )

            if response.text:
                output = AccessibilityOutput.model_validate_json(response.text)
                logger.info(f"Accessibility package compiled. Alt text: '{output.alt_text}' (Score: {output.accessibility_score.overall_score}).")
                return output
            else:
                raise ValueError("Empty response text returned by the model.")

        except APIError as api_err:
            logger.error(f"Gemini API call failed during accessibility profiling: {api_err}. Using fallback.", exc_info=True)
            return self._get_fallback_output(f"API Error: {str(api_err)}")
        except Exception as exc:
            logger.error(f"Failed to compile accessibility details or parse response: {exc}. Using fallback.", exc_info=True)
            return self._get_fallback_output(f"Processing Failure: {str(exc)}")

    def _get_fallback_output(self, error_message: str) -> AccessibilityOutput:
        """
        Builds a safe fallback accessibility package when model calls cannot execute.
        """
        return AccessibilityOutput(
            screen_reader_description="Screen reader description not available due to system processing error.",
            easy_english_version="Description is not ready yet.",
            child_friendly_version="We couldn't load the description right now.",
            audio_narration_script="Audio guide is currently offline.",
            alt_text="uncertain alt text",
            object_list=[],
            spatial_layout_description="Spatial details are unavailable.",
            accessibility_score=AccessibilityScoreDetails(
                completeness=0.0,
                readability=0.0,
                usefulness=0.0,
                screen_reader_compatibility=0.0,
                overall_score=0.0
            ),
            suggested_improvements=["Check system logs and try re-uploading the file."],
            confidence_score=0.0,
            reasoning=f"Fallback profile triggered due to execution error: {error_message}"
        )

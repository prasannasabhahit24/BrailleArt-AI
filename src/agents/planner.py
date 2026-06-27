"""
planner.py

Planner Agent for BrailleArt AI.
Responsibility:
Inspects uploaded artwork metadata and the user request, then dynamically decides 
which specialized agents should execute, and in what sequence.
Returns a structured execution plan as a JSON-compatible Pydantic model.
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
logger = setup_logger("brailleart_ai.planner")

# Load environment variables
load_dotenv()

class PlannerInput(BaseModel):
    """Input parameters for the Planner Agent."""
    user_request: str = Field(..., description="The user prompt or query describing what they want to achieve.")
    has_image: bool = Field(default=False, description="Flag indicating if the user has uploaded an image payload.")
    image_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata (e.g. filename, size, claimed mime type).")
    context_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context parameters (e.g. user learning level).")

class PlannerOutput(BaseModel):
    """Structured execution plan output schema."""
    execution_plan: List[str] = Field(..., description="Ordered list of agent identifiers representing the execution plan.")
    reason: str = Field(..., description="Justification statement explaining why this sequence was selected and why other agents were skipped.")

class PlannerAgent:
    """
    Planner Agent orchestrator using Google Gen AI ADK and Gemini 2.5 Flash.
    """

    def __init__(self, client: Optional[genai.Client] = None):
        """
        Initializes the PlannerAgent with an optional pre-configured Gemini client.
        If no client is provided, instantiates a new client using environment credentials.
        """
        self._client = client
        self.system_prompt = (
            "You are the Planner Agent for BrailleArt AI.\n"
            "Your task is to inspect the user's request and any uploaded artwork metadata, "
            "and dynamically decide which specialized agents should execute. Your decision should "
            "be optimal, skipping unnecessary agents when appropriate.\n\n"
            "Supported agent identifiers:\n"
            "- security: Mandatory for any file upload or raw input checks.\n"
            "- vision: Processes spatial shape structure, layout, contour boundaries (requires image).\n"
            "- ocr: Extracts written letters/annotations inside images (skip if no text is present).\n"
            "- style: Computes rendering thresholds, line weights, or dithering settings.\n"
            "- emotion: Analyzes mood/tone to suggest stylistic adjustments (shading, spacing).\n"
            "- art_knowledge: Identifies artists, historical context, symbolism, similar works.\n"
            "- accessibility: Generates screen-reader scripts, child descriptions, alt text, Easy English.\n"
            "- evaluation: Audits visual-to-tactile alignment and outputs grading metrics.\n"
            "- braille: Translates accessibility agent outputs into Grade 1, Grade 2, and Unicode Braille representations.\n"
            "- tactile: Generates simplified SVG outlines, raised-line layouts, boundary maps, relative spatial positions, and embosser-ready SVGs based on prior agent signals.\n"
            "- learning: Customizes grading level or explanation vocabulary.\n"
            "- reflection: Critiques intermediate drafts to remove dot overcrowding.\n"
            "- explainability: Compiles a report justifying confidence scores and choices.\n"
            "- conversation: Manages normal dialogue flow or conversational feedback.\n\n"
            "Rules:\n"
            "1. If an image is uploaded, you MUST include 'security', 'vision', 'style', 'tactile', 'accessibility', and 'braille'.\n"
            "2. If the user asks about an artwork's meaning, artist, or history, include 'art_knowledge'.\n"
            "3. Include 'braille' to convert accessibility outputs or text inputs into Braille patterns.\n"
            "4. Order the execution list logically (e.g. security -> learning/profile checks -> visual analysis -> style/emotion adjustments -> accessibility -> braille -> tactile -> explainability/evaluation audits).\n"
            "5. Skip agents that are completely unrelated to the request."
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

    async def generate_plan(self, input_data: PlannerInput) -> PlannerOutput:
        """
        Dynamically analyzes inputs and returns a structured agent execution plan.
        Includes a robust fallback mechanism in case of network or API exceptions.
        
        Args:
            input_data (PlannerInput): Prompt and image metadata parameters.
            
        Returns:
            PlannerOutput: Validated execution plan and reasoning.
        """
        logger.info(f"Generating execution plan for request: '{input_data.user_request}' (has_image: {input_data.has_image})")

        try:
            # Build payload contents for the model
            contents = [
                f"User Request: {input_data.user_request}\n"
                f"Has Image: {input_data.has_image}\n"
                f"Image Metadata: {input_data.image_metadata}\n"
                f"Context Metadata: {input_data.context_metadata}"
            ]

            # Generate content using Gemini 2.5 Flash
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=PlannerOutput,
                    system_instruction=self.system_prompt,
                    temperature=0.1
                )
            )

            # Parse and validate the response
            if response.text:
                plan = PlannerOutput.model_validate_json(response.text)
                logger.info(f"Generated plan via LLM successfully. Steps: {plan.execution_plan}")
                return plan
            else:
                raise ValueError("Empty response received from the Gemini model.")

        except APIError as api_err:
            logger.error(f"Gemini API error occurred: {api_err}. Activating static fallback plan.", exc_info=True)
            return self._fallback_plan(input_data, f"Gemini API Error: {str(api_err)}")
        except Exception as exc:
            logger.error(f"Unexpected error during plan generation: {exc}. Activating static fallback plan.", exc_info=True)
            return self._fallback_plan(input_data, f"Internal Error: {str(exc)}")

    def _fallback_plan(self, input_data: PlannerInput, error_reason: str) -> PlannerOutput:
        """
        Builds a safe, static fallback execution sequence based on structural input characteristics.
        """
        plan = []
        if input_data.has_image:
            # Standard sequence for visual inputs
            plan = ["security", "learning", "vision", "style", "accessibility", "braille", "tactile", "explainability"]
            # Scan query to see if art details are relevant
            lowered_req = input_data.user_request.lower()
            if any(k in lowered_req for k in ["artist", "who painted", "symbolism", "context", "history", "museum"]):
                plan.insert(4, "art_knowledge")
            if any(k in lowered_req for k in ["text", "ocr", "words", "letters", "label"]):
                plan.insert(3, "ocr")
        else:
            # Text-only translation path
            plan = ["security", "learning", "braille", "conversation", "explainability"]

        return PlannerOutput(
            execution_plan=plan,
            reason=f"Static fallback plan activated due to model processing issue ({error_reason})."
        )

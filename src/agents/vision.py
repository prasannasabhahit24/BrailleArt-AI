"""
vision.py

Vision Agent for BrailleArt AI.
Responsibility:
Analyzes visual artworks using Gemini 2.5 Flash.
Detects objects, people, colors, lighting, composition, perspective, artistic elements,
and dominant regions.
Returns structured JSON data matching the Pydantic validation schema, including 
confidence scores and detailed observations/reasoning.
"""

import os
import io
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import APIError
from PIL import Image
from dotenv import load_dotenv

from ..utils.helpers import setup_logger

# Initialize logging
logger = setup_logger("brailleart_ai.vision")

# Load environment variables
load_dotenv()

class DetectedObject(BaseModel):
    """An object, feature, or person detected within the artwork."""
    label: str = Field(..., description="Name of the detected object, shape, or person.")
    bounding_box: Optional[List[float]] = Field(None, description="Normalized coordinates [ymin, xmin, ymax, xmax] of the object boundary.")
    color_profile: List[str] = Field(..., description="Primary colors observed on this specific element.")
    reasoning: str = Field(..., description="Observation notes justifying why this object was classified.")
    confidence: float = Field(..., description="Confidence score for this detection, from 0.0 to 1.0.")

class ColorAnalysis(BaseModel):
    """Detailed color and light configuration details."""
    dominant_colors: List[str] = Field(..., description="List of primary and secondary colors prominent in the artwork.")
    lighting_description: str = Field(..., description="Evaluation of the light source direction, intensity, and shadow effects.")
    contrast_level: str = Field(..., description="Overall contrast rating: 'high', 'medium', or 'low'.")

class CompositionAnalysis(BaseModel):
    """Structural layout and perspective attributes."""
    perspective: str = Field(..., description="Visual perspective classification (e.g. linear, atmospheric, flat, isometric).")
    composition_rules: List[str] = Field(..., description="Observed layout design styles (e.g. rule of thirds, central symmetry, balance).")
    artistic_elements: List[str] = Field(..., description="Dominant artistic design tools used (e.g. bold outlines, smooth textures, geometric forms).")
    dominant_regions: List[str] = Field(..., description="Segmentation description of major regions (e.g. foreground figure, sky boundary).")

class VisionInput(BaseModel):
    """Input payload containing raw image data and focus settings."""
    image_bytes: bytes = Field(..., description="Raw binary data of the uploaded image file.")
    focus_areas: Optional[List[str]] = Field(default=None, description="User-specified focal areas to prioritize during inspection.")

class VisionOutput(BaseModel):
    """Comprehensive visual profiling output."""
    detected_items: List[DetectedObject] = Field(..., description="Structured catalog of visual elements.")
    color_analysis: ColorAnalysis = Field(..., description="Evaluated color palette and lighting characteristics.")
    composition_analysis: CompositionAnalysis = Field(..., description="Evaluated visual structure and geometry rules.")
    overall_summary: str = Field(..., description="A concise narrative summary describing the visual content of the artwork.")
    confidence_score: float = Field(..., description="Overall confidence rating in this visual assessment, from 0.0 to 1.0.")

class VisionAgent:
    """
    VisionAgent class using Google Gen AI ADK to run multi-modal visual analysis.
    """

    def __init__(self, client: Optional[genai.Client] = None):
        """
        Initializes the VisionAgent with an optional pre-configured Gemini client.
        If no client is provided, checks environment variables and instantiates a new client.
        """
        self._client = client
        self.system_prompt = (
            "You are the Vision Agent for BrailleArt AI.\n"
            "Your task is to analyze the provided image of an artwork and extract structured spatial information.\n\n"
            "Identify:\n"
            "1. Objects and people (including names, bounding boxes if possible, color profiles, confidence, and reasoning).\n"
            "2. Color palette (dominant colors, light directions/source description, contrast rating).\n"
            "3. Composition and perspective (e.g. rules of thirds, depth perspective, design elements like textures or forms, and dominant regions).\n"
            "4. A summary of the scene content.\n\n"
            "Ensure the output conforms exactly to the requested JSON response schema."
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

    async def analyze_image(self, input_data: VisionInput) -> VisionOutput:
        """
        Performs visual feature extraction on image bytes asynchronously.
        Provides a static fallback model if client calls or serialization fails.
        
        Args:
            input_data (VisionInput): Bytes representing the image.
            
        Returns:
            VisionOutput: Structured profile of objects, colors, and layout.
        """
        logger.info(f"Received request for visual analysis (bytes size: {len(input_data.image_bytes)}).")

        if not input_data.image_bytes:
            logger.error("Empty image bytes payload provided.")
            return self._get_fallback_output("Missing input: Image bytes array was empty.")

        try:
            # Try to load bytes into a PIL Image to verify file integrity
            image = Image.open(io.BytesIO(input_data.image_bytes))
            logger.info(f"Loaded image successfully. Format: {image.format}, Size: {image.size}")

            # Define prompt payload for the multimodal call
            prompt = "Analyze this artwork in detail. Extract objects, colors, lighting, composition details, and regions."
            if input_data.focus_areas:
                prompt += f" Pay special attention to these focus areas: {', '.join(input_data.focus_areas)}."

            # Invoke Gemini 2.5 Flash
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[image, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=VisionOutput,
                    system_instruction=self.system_prompt,
                    temperature=0.1
                )
            )

            if response.text:
                output = VisionOutput.model_validate_json(response.text)
                logger.info(f"Visual analysis generated successfully. Detected items count: {len(output.detected_items)}.")
                return output
            else:
                raise ValueError("Empty response text returned by the model.")

        except APIError as api_err:
            logger.error(f"Gemini API call failed during visual analysis: {api_err}. Using fallback.", exc_info=True)
            return self._get_fallback_output(f"API Error: {str(api_err)}")
        except Exception as exc:
            logger.error(f"Failed to process image or parse model response: {exc}. Using fallback.", exc_info=True)
            return self._get_fallback_output(f"Processing Failure: {str(exc)}")

    def _get_fallback_output(self, error_message: str) -> VisionOutput:
        """
        Builds a safe fallback visual profile when model calls cannot execute.
        """
        return VisionOutput(
            detected_items=[
                DetectedObject(
                    label="Generic Outline Box",
                    bounding_box=[0.0, 0.0, 1.0, 1.0],
                    color_profile=["monochrome"],
                    reasoning=f"Default outline created due to image processing failure: {error_message}.",
                    confidence=0.5
                )
            ],
            color_analysis=ColorAnalysis(
                dominant_colors=["black", "white"],
                lighting_description="Default flat lighting.",
                contrast_level="medium"
            ),
            composition_analysis=CompositionAnalysis(
                perspective="flat",
                composition_rules=["centered"],
                artistic_elements=["geometric outlines"],
                dominant_regions=["entire layout"]
            ),
            overall_summary="Simplified visual frame generated due to processing error.",
            confidence_score=0.5
        )

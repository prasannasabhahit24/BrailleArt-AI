"""
ocr.py

OCR Agent for BrailleArt AI.
Responsibility:
Performs Optical Character Recognition (OCR) on uploaded image bytes.
Extracts visible text, labels, signatures, and titles from artwork.
Detects languages, translates to English when necessary, returns text bounding boxes,
and handles images without text gracefully.
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
logger = setup_logger("brailleart_ai.ocr")

# Load environment variables
load_dotenv()

class OCRTextSegment(BaseModel):
    """A single segment of detected text with metadata and translation."""
    text: str = Field(..., description="The raw extracted text string.")
    bounding_box: Optional[List[float]] = Field(None, description="Normalized coordinates [ymin, xmin, ymax, xmax] outlining the text area.")
    detected_language: str = Field(..., description="The detected language name or ISO code (e.g. 'es', 'fr', 'en').")
    translated_text: Optional[str] = Field(None, description="English translation of the raw text snippet, if not originally in English.")
    confidence: float = Field(..., description="Confidence score for this detection, from 0.0 to 1.0.")
    reasoning: str = Field(..., description="Observational reasoning justifying the extraction or translation.")

class OCRInput(BaseModel):
    """Input payload containing raw image bytes."""
    image_bytes: bytes = Field(..., description="Raw binary data of the uploader image file.")

class OCROutput(BaseModel):
    """Structured response detailing extracted text metadata."""
    text_segments: List[OCRTextSegment] = Field(..., description="A list of all individual text regions identified.")
    combined_text: str = Field(..., description="All extracted text segments aggregated in logical reading order.")
    has_text: bool = Field(..., description="Flag indicating if any readable text was detected.")
    confidence_score: float = Field(..., description="Overall confidence rating in this OCR process, from 0.0 to 1.0.")

class OCRAgent:
    """
    OCRAgent class utilizing Gemini 2.5 Flash vision capabilities to execute multilingual text extraction.
    """

    def __init__(self, client: Optional[genai.Client] = None):
        """
        Initializes the OCRAgent with an optional pre-configured Gemini client.
        If no client is provided, checks environment variables and instantiates a new client.
        """
        self._client = client
        self.system_prompt = (
            "You are the OCR Agent for BrailleArt AI.\n"
            "Your task is to detect and extract all visible text from the uploaded artwork.\n\n"
            "Analyze the image and return a JSON matching the requested schema with:\n"
            "1. List of text segments (raw text, normalized bounding boxes, language code, "
            "English translation if multilingual, confidence score, and reasoning).\n"
            "2. Combined text in normal reading order.\n"
            "3. 'has_text' flag indicating if any text exists.\n"
            "4. Overall confidence score (0.0 to 1.0).\n\n"
            "If no text is visible, return an empty 'text_segments' list, an empty 'combined_text' string, "
            "and set 'has_text' to false with a confidence score reflecting your certainty."
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

    async def extract_text(self, input_data: OCRInput) -> OCROutput:
        """
        Performs visual text extraction on uploader image bytes asynchronously.
        Provides a static fallback model if model calls or serialization fails.
        
        Args:
            input_data (OCRInput): Raw image data payload.
            
        Returns:
            OCROutput: Catalog of text snippets, languages, and locations.
        """
        logger.info(f"Received request for OCR text extraction (bytes size: {len(input_data.image_bytes)}).")

        if not input_data.image_bytes:
            logger.error("Empty image bytes payload provided.")
            return self._get_fallback_output("Missing input: Image bytes array was empty.")

        try:
            # Validate image file integrity
            image = Image.open(io.BytesIO(input_data.image_bytes))
            logger.info(f"Loaded image successfully. Format: {image.format}, Size: {image.size}")

            # Define prompt payload for multimodal model
            prompt = "Extract all text annotations, labels, signatures, titles, and captions visible in this image."

            # Invoke Gemini 2.5 Flash
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[image, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=OCROutput,
                    system_instruction=self.system_prompt,
                    temperature=0.1
                )
            )

            if response.text:
                output = OCROutput.model_validate_json(response.text)
                logger.info(f"OCR text extraction completed. segments count: {len(output.text_segments)}, has_text: {output.has_text}.")
                return output
            else:
                raise ValueError("Empty response text returned by the model.")

        except APIError as api_err:
            logger.error(f"Gemini API call failed during OCR text extraction: {api_err}. Using fallback.", exc_info=True)
            return self._get_fallback_output(f"API Error: {str(api_err)}")
        except Exception as exc:
            logger.error(f"Failed to process image or parse OCR response: {exc}. Using fallback.", exc_info=True)
            return self._get_fallback_output(f"Processing Failure: {str(exc)}")

    def _get_fallback_output(self, error_message: str) -> OCROutput:
        """
        Builds a safe fallback OCR profile when model calls cannot execute.
        """
        return OCROutput(
            text_segments=[],
            combined_text="",
            has_text=False,
            confidence_score=1.0
        )

"""
art_knowledge.py

Art Knowledge Agent for BrailleArt AI.
Responsibility:
Identifies famous artworks and details artist, art movement, artistic medium,
symbolism, historical context, cultural significance, and recommendations.
Handles unknown or low-confidence artworks gracefully by returning 'unknown artwork' 
and explaining why.
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

# Initialize logging
logger = logging.getLogger("brailleart_ai.art_knowledge")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Load environment variables
load_dotenv()

class SymbolismItem(BaseModel):
    """Specific symbolic element identified in the art."""
    element: str = Field(..., description="The symbol or visual motif identified.")
    meaning: str = Field(..., description="The meaning or representation of this symbol.")
    reasoning: str = Field(..., description="The justification or visual evidence for this symbol interpretation.")

class SimilarArtwork(BaseModel):
    """Related or similar artwork recommendation."""
    title: str = Field(..., description="Title of the recommended similar artwork.")
    artist: str = Field(..., description="Artist of the similar work.")
    comparison: str = Field(..., description="Why this work is compared or related (visual style, theme, or epoch similarities).")

class ArtKnowledgeInput(BaseModel):
    """Input payload containing raw image data."""
    image_bytes: bytes = Field(..., description="Raw binary data of the uploaded image file.")

class ArtKnowledgeOutput(BaseModel):
    """Structured documentation detailing art history context."""
    artwork_title: str = Field(..., description="Identified title of the artwork. Set to exactly 'unknown artwork' if not recognized or confidence is low.")
    artist: str = Field(..., description="Name of the artist. Set to 'unknown artist' if not identified.")
    art_movement: str = Field(..., description="The historical art movement or style category (e.g. Impressionism, Renaissance).")
    medium: str = Field(..., description="The artistic medium used (e.g. oil on canvas, digital painting, sketch).")
    estimated_year: str = Field(..., description="The estimated or exact year or time period of creation.")
    symbolism: List[SymbolismItem] = Field(..., description="List of identified symbolic visual items and their historical significance.")
    historical_context: str = Field(..., description="The historical background, circumstances, and setting under which the art was made.")
    cultural_significance: str = Field(..., description="Why the artwork is culturally important, its legacy, or social influence.")
    similar_artworks: List[SimilarArtwork] = Field(..., description="List of similar or related artworks recommended for comparison.")
    confidence_score: float = Field(..., description="Confidence score in the overall identification, from 0.0 to 1.0.")
    reasoning: str = Field(..., description="Detailed reasoning explaining the identification conclusion and details.")

class ArtKnowledgeAgent:
    """
    ArtKnowledgeAgent class utilizing Gemini 2.5 Flash to retrieve artistic context and identify artwork.
    """

    def __init__(self, client: Optional[genai.Client] = None):
        """
        Initializes the ArtKnowledgeAgent with an optional pre-configured Gemini client.
        If no client is provided, checks environment variables and instantiates a new client.
        """
        self._client = client
        self.system_prompt = (
            "You are the Art Knowledge Agent for BrailleArt AI.\n"
            "Your role is to identify fine art, paintings, and drawings from visual input, "
            "providing accurate context regarding creator, movement, medium, estimated year, "
            "motifs, history, and legacy. Do not invent details.\n\n"
            "Rules for identification confidence:\n"
            "1. If you are not highly confident (confidence < 0.70) in identifying the specific "
            "artwork title and artist, you MUST return exactly 'unknown artwork' in the artwork_title field "
            "and 'unknown artist' in the artist field. Explain why the artwork is unknown in the reasoning field "
            "(e.g., standard digital sketch, family photo, modern user drawing, low-quality capture).\n"
            "2. Never hallucinate or inventory false history. If certain facts are not known, represent them as 'unknown'.\n"
            "3. If the image is a custom sketch, modern digital work, or non-famous artifact, set 'artwork_title' "
            "to 'unknown artwork' and categorize the style and visual elements as appropriate in reasoning."
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

    async def identify_artwork(self, input_data: ArtKnowledgeInput) -> ArtKnowledgeOutput:
        """
        Processes image bytes, identifies artwork, and outputs Pydantic metadata.
        Provides a static fallback model if model calls or serialization fails.
        
        Args:
            input_data (ArtKnowledgeInput): Image bytes of the artwork.
            
        Returns:
            ArtKnowledgeOutput: Art history report.
        """
        logger.info(f"Received request for art identification (bytes size: {len(input_data.image_bytes)}).")

        if not input_data.image_bytes:
            logger.error("Empty image bytes payload provided.")
            return self._get_fallback_output("Missing input: Image bytes array was empty.")

        try:
            # Validate image file integrity
            image = Image.open(io.BytesIO(input_data.image_bytes))
            logger.info(f"Loaded image successfully. Format: {image.format}, Size: {image.size}")

            # Define prompt payload for multimodal model
            prompt = "Identify this image, artist, medium, history, and symbolism."

            # Invoke Gemini 2.5 Flash
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[image, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ArtKnowledgeOutput,
                    system_instruction=self.system_prompt,
                    temperature=0.1
                )
            )

            if response.text:
                output = ArtKnowledgeOutput.model_validate_json(response.text)
                logger.info(f"Art identification completed. Identified: {output.artwork_title} by {output.artist} (Confidence: {output.confidence_score}).")
                return output
            else:
                raise ValueError("Empty response text returned by the model.")

        except APIError as api_err:
            logger.error(f"Gemini API call failed during art identification: {api_err}. Using fallback.", exc_info=True)
            return self._get_fallback_output(f"API Error: {str(api_err)}")
        except Exception as exc:
            logger.error(f"Failed to process image or parse art identification response: {exc}. Using fallback.", exc_info=True)
            return self._get_fallback_output(f"Processing Failure: {str(exc)}")

    def _get_fallback_output(self, error_message: str) -> ArtKnowledgeOutput:
        """
        Builds a safe fallback art profile when model calls cannot execute.
        """
        return ArtKnowledgeOutput(
            artwork_title="unknown artwork",
            artist="unknown artist",
            art_movement="unknown",
            medium="unknown",
            estimated_year="unknown",
            symbolism=[],
            historical_context="No historical details available.",
            cultural_significance="No cultural details available.",
            similar_artworks=[],
            confidence_score=0.0,
            reasoning=f"Fallback profile triggered due to execution error: {error_message}"
        )

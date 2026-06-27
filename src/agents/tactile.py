"""
tactile.py

Tactile Agent for BrailleArt AI.
Responsibility:
Generates simplified SVG outlines, raised-line layouts, boundary maps, 
relative spatial positions, and embosser-ready SVGs based on prior agent signals 
(Vision, OCR, Accessibility, Braille). Saves generated SVGs to local outputs 
and details metadata.
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv

from ..utils.helpers import setup_logger

# Initialize logging
logger = setup_logger("brailleart_ai.tactile")

# Load environment variables
load_dotenv()

class TactileInput(BaseModel):
    """Input payload containing prior agent outputs for tactile layout generation."""
    vision_output: Optional[Dict[str, Any]] = Field(default=None, description="Output dictionary from Vision Agent.")
    ocr_output: Optional[Dict[str, Any]] = Field(default=None, description="Output dictionary from OCR Agent.")
    accessibility_output: Optional[Dict[str, Any]] = Field(default=None, description="Output dictionary from Accessibility Agent.")
    braille_output: Optional[Dict[str, Any]] = Field(default=None, description="Output dictionary from Braille Agent.")
    session_id: Optional[str] = Field(default="default-session", description="Session ID identifier.")

class TactileOutput(BaseModel):
    """Tactile layout output containing SVGs, boundary maps, and coordinates."""
    simplified_svg: str = Field(..., description="Simplified SVG outline code of the artwork.")
    raised_line_layout: str = Field(..., description="Details/description of raised-line layout coordinates.")
    object_boundary_map: Dict[str, Any] = Field(..., description="Map of object boundary coordinates.")
    relative_spatial_positions: Dict[str, Any] = Field(..., description="Relative positions of major objects.")
    braille_overlay_coordinates: Dict[str, Any] = Field(..., description="Coordinates mapping Braille overlay locations.")
    embosser_ready_svg: str = Field(..., description="SVG optimized for tactile printers/embossers (e.g. raised dots/lines).")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata including file paths and execution parameters.")
    confidence_score: float = Field(..., description="Fidelity score of tactile graphics rendering (0.0 to 1.0).")

class TactileAgent:
    """
    TactileAgent class generating tactile SVGs and coordinate mappings.
    Uses Google Gen AI ADK and Gemini 2.5 Flash.
    """

    def __init__(self, client: Optional[genai.Client] = None):
        """
        Initializes the TactileAgent with an optional pre-configured Gemini client.
        """
        self._client = client
        self.system_prompt = (
            "You are the Tactile Agent for BrailleArt AI.\n"
            "Your task is to synthesize image outputs (Vision, OCR, Accessibility, Braille) "
            "and generate a tactile-accessible graphic package containing SVGs and coordinate maps.\n\n"
            "Analyze the inputs and return a JSON matching the requested schema with:\n"
            "1. simplified_svg: An inline SVG string containing simple paths outlining major contours.\n"
            "2. raised_line_layout: Explanation or dot/dash code representation of the raised line design.\n"
            "3. object_boundary_map: A dictionary matching labels to bounding coordinates (e.g. {label: [x, y, w, h]}).\n"
            "4. relative_spatial_positions: A dictionary explaining spatial layout positions (e.g., center, top-left).\n"
            "5. braille_overlay_coordinates: Coordinates indicating where Braille labels should be overlaid on the SVG.\n"
            "6. embosser_ready_svg: SVG code optimized for embossers/tactile printers (typically using high contrast paths and dashed dots).\n"
            "7. confidence_score: Confidence score representing tactile accuracy (0.0 to 1.0).\n\n"
            "Fallback rules:\n"
            "If inputs are invalid or empty, set confidence_score to 0.0, and return placeholders or empty lists for SVGs."
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

    async def generate_tactile_layout(self, input_data: TactileInput) -> TactileOutput:
        """
        Generates SVGs and boundary layouts asynchronously based on sub-agent data.
        Saves output SVGs locally to outputs/ folder.
        
        Args:
            input_data (TactileInput): Accumulated signals from other agents.
            
        Returns:
            TactileOutput: Rendered graphics schemas and file export details.
        """
        logger.info(f"Tactile layout generation started. Session ID: {input_data.session_id}")

        # Check for empty/invalid inputs
        if not any([input_data.vision_output, input_data.ocr_output,
                    input_data.accessibility_output, input_data.braille_output]):
            logger.warning("Empty input data dictionary package. Using fallback.")
            return self._get_fallback_output("Missing inputs: All sub-agent outputs are empty.")

        try:
            # Package contexts for prompt evaluation
            contents = [
                f"Vision Agent Output: {input_data.vision_output}\n"
                f"OCR Agent Output: {input_data.ocr_output}\n"
                f"Accessibility Agent Output: {input_data.accessibility_output}\n"
                f"Braille Agent Output: {input_data.braille_output}"
            ]

            # Invoke Gemini 2.5 Flash
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TactileOutput,
                    system_instruction=self.system_prompt,
                    temperature=0.1
                )
            )

            if response.text:
                output = TactileOutput.model_validate_json(response.text)

                # Write generated SVGs to the workspace
                os.makedirs("outputs", exist_ok=True)
                timestamp = int(time.time())
                svg_simp_name = f"outputs/tactile_simplified_{input_data.session_id}_{timestamp}.svg"
                svg_emb_name = f"outputs/tactile_embosser_{input_data.session_id}_{timestamp}.svg"

                try:
                    with open(svg_simp_name, "w", encoding="utf-8") as f:
                        f.write(output.simplified_svg)
                    output.metadata["simplified_svg_path"] = svg_simp_name
                    logger.info(f"Simplified SVG layout exported: {svg_simp_name}")
                except Exception as svg_err:
                    logger.error(f"Failed to write simplified SVG file: {svg_err}")
                    output.metadata["simplified_svg_path"] = None

                try:
                    with open(svg_emb_name, "w", encoding="utf-8") as f:
                        f.write(output.embosser_ready_svg)
                    output.metadata["embosser_ready_svg_path"] = svg_emb_name
                    logger.info(f"Embosser SVG layout exported: {svg_emb_name}")
                except Exception as svg_err:
                    logger.error(f"Failed to write embosser SVG file: {svg_err}")
                    output.metadata["embosser_ready_svg_path"] = None

                return output
            else:
                raise ValueError("Empty response text returned by model.")

        except APIError as api_err:
            logger.error(f"Gemini API call failed during tactile layout generation: {api_err}. Using fallback.", exc_info=True)
            return self._get_fallback_output(f"API Error: {str(api_err)}")
        except Exception as exc:
            logger.error(f"Failed to generate layout or parse response: {exc}. Using fallback.", exc_info=True)
            return self._get_fallback_output(f"Processing Failure: {str(exc)}")

    def _get_fallback_output(self, error_message: str) -> TactileOutput:
        """
        Builds a safe fallback Tactile layout package.
        """
        empty_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="none" stroke="red" stroke-width="2" /></svg>'
        return TactileOutput(
            simplified_svg=empty_svg,
            raised_line_layout="Raised lines details not available due to processing error.",
            object_boundary_map={},
            relative_spatial_positions={},
            braille_overlay_coordinates={},
            embosser_ready_svg=empty_svg,
            metadata={"fallback_active": True, "error": error_message, "simplified_svg_path": None, "embosser_ready_svg_path": None},
            confidence_score=0.0
        )

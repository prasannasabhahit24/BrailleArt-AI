"""
braille.py

Braille Agent for BrailleArt AI.
Responsibility:
Handles language-to-Braille translations, supporting Grade 1 (letter-by-letter) 
and Grade 2 (contracted) Braille standards.
Ensures descriptions, alt text, and label collections from the Accessibility Agent 
are correctly formatted in standard Braille unicode cells, applying indicators 
(e.g. capital letters, numbers) and exporting a downloadable .txt file.
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

# Initialize logging
logger = logging.getLogger("brailleart_ai.braille")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Load environment variables
load_dotenv()

class BrailleInput(BaseModel):
    """Input payload containing accessibility agent output fields for translation."""
    screen_reader_description: Optional[str] = Field(default="", description="Screen reader description from accessibility agent.")
    easy_english_version: Optional[str] = Field(default="", description="Easy English version from accessibility agent.")
    child_friendly_version: Optional[str] = Field(default="", description="Child-friendly version from accessibility agent.")
    alt_text: Optional[str] = Field(default="", description="Alt text from accessibility agent.")
    object_list: List[str] = Field(default_factory=list, description="Object list from accessibility agent.")
    session_id: Optional[str] = Field(default="default-session", description="Session identifier for output file organization.")

class BrailleOutput(BaseModel):
    """Result of textual Braille translation, structured as requested."""
    grade1_braille: str = Field(..., description="Grade 1 (uncontracted) Braille translation text.")
    grade2_braille: str = Field(..., description="Grade 2 (contracted) Braille translation text if supported.")
    unicode_braille: str = Field(..., description="Braille translated into Unicode Braille Patterns.")
    plain_text: str = Field(..., description="Plain text representation of the source content translated.")
    character_count: int = Field(..., description="Total count of characters or cells generated.")
    translation_notes: str = Field(..., description="Detailed translation notes, contraction rules applied, or warnings.")
    confidence_score: float = Field(..., description="Translation confidence score from 0.0 to 1.0.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary containing file paths and details.")

class BrailleAgent:
    """
    BrailleAgent class translating accessibility descriptions to Braille.
    Uses Google Gen AI ADK and Gemini 2.5 Flash.
    """

    def __init__(self, client: Optional[genai.Client] = None):
        """
        Initializes the BrailleAgent with an optional pre-configured Gemini client.
        If no client is provided, checks environment variables and instantiates a new client.
        """
        self._client = client
        self.system_prompt = (
            "You are the Braille Agent for BrailleArt AI.\n"
            "Your task is to take descriptive visual texts (screen reader descriptions, alt text, etc.) "
            "and translate them into Braille formats complying with Unified English Braille (UEB) guidelines.\n\n"
            "Analyze the input and return a JSON matching the requested schema with:\n"
            "1. grade1_braille: Uncontracted Grade 1 Braille using standard dots or English characters.\n"
            "2. grade2_braille: Contracted Grade 2 Braille applying contractions (such as 'the', 'and', 'ing', etc.).\n"
            "3. unicode_braille: Standard Unicode Braille Patterns block representations (e.g., ⠠⠓⠑⠇⠇⠕).\n"
            "4. plain_text: The primary English text source being translated.\n"
            "5. character_count: Total cell/character count in the unicode braille string.\n"
            "6. translation_notes: Notes outlining applied rules, capital/number indicators, or skipped elements.\n"
            "7. confidence_score: Confidence rating of the translation (0.0 to 1.0).\n\n"
            "Low-confidence rules:\n"
            "If the input data is empty, invalid, or corrupted, set confidence_score to 0.0, "
            "populate translation_notes with explanation of the failure, and return empty strings for the Braille patterns."
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

    async def translate(self, input_data: BrailleInput) -> BrailleOutput:
        """
        Translates accessibility descriptions into Grade 1, Grade 2, and Unicode Braille patterns.
        Saves a downloadable copy of the translation to the local outputs directory.
        
        Args:
            input_data (BrailleInput): Text data payload and options from accessibility agent.
            
        Returns:
            BrailleOutput: Translated patterns, character metrics, and file output metadata.
        """
        logger.info(f"Received translation request. Session ID: {input_data.session_id}")

        # Check for empty/invalid inputs
        if not any([input_data.screen_reader_description, input_data.easy_english_version,
                    input_data.child_friendly_version, input_data.alt_text, input_data.object_list]):
            logger.warning("Empty accessibility input fields provided. Triggering fallback output.")
            return self._get_fallback_output("Missing inputs: All accessibility text fields and object lists are empty.")

        try:
            # Package fields for model prompt
            contents = [
                f"Screen Reader Description: {input_data.screen_reader_description}\n"
                f"Easy English Version: {input_data.easy_english_version}\n"
                f"Child Friendly Version: {input_data.child_friendly_version}\n"
                f"Alt Text: {input_data.alt_text}\n"
                f"Object List: {', '.join(input_data.object_list) if input_data.object_list else 'None'}"
            ]

            # Invoke Gemini 2.5 Flash using structured output
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=BrailleOutput,
                    system_instruction=self.system_prompt,
                    temperature=0.1
                )
            )

            if response.text:
                output = BrailleOutput.model_validate_json(response.text)
                
                # Write translation to a downloadable text file in the workspace
                os.makedirs("outputs", exist_ok=True)
                file_name = f"outputs/braille_{input_data.session_id}_{int(time.time())}.txt"
                
                try:
                    with open(file_name, "w", encoding="utf-8") as f:
                        f.write("=== Braille Translation Export ===\n")
                        f.write(f"Session ID: {input_data.session_id}\n")
                        f.write(f"Plain Text Source: {output.plain_text}\n\n")
                        f.write(f"Grade 1 Braille:\n{output.grade1_braille}\n\n")
                        f.write(f"Grade 2 Braille:\n{output.grade2_braille}\n\n")
                        f.write(f"Unicode Braille:\n{output.unicode_braille}\n\n")
                        f.write(f"Translation Notes: {output.translation_notes}\n")
                    logger.info(f"Braille translation saved to file: {file_name}")
                    output.metadata["download_file_path"] = file_name
                except Exception as write_err:
                    logger.error(f"Failed to write downloadable translation file: {write_err}")
                    output.metadata["download_file_path"] = None
                    output.metadata["file_write_error"] = str(write_err)

                return output
            else:
                raise ValueError("Empty response text returned by the Gemini model.")

        except APIError as api_err:
            logger.error(f"Gemini API call failed during Braille translation: {api_err}. Using fallback.", exc_info=True)
            return self._get_fallback_output(f"API Error: {str(api_err)}")
        except Exception as exc:
            logger.error(f"Failed to compile Braille translation or parse response: {exc}. Using fallback.", exc_info=True)
            return self._get_fallback_output(f"Processing Failure: {str(exc)}")

    def _get_fallback_output(self, error_message: str) -> BrailleOutput:
        """
        Builds a safe fallback Braille package when model calls or validations fail.
        """
        return BrailleOutput(
            grade1_braille="",
            grade2_braille="",
            unicode_braille="",
            plain_text="Error: Could not retrieve translation content.",
            character_count=0,
            translation_notes=f"Fallback triggered due to error: {error_message}",
            confidence_score=0.0,
            metadata={"download_file_path": None, "fallback_active": True}
        )

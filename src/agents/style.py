"""
style.py

Style Agent for BrailleArt AI.
Responsibility:
Configures the style parameters (minimalist, detailed, filled, outline-only) 
to match the user's tactile reading goals.
Determines border patterns, line weights, shading dot densities (Floyd-Steinberg vs Bayer), 
and resolution options to make the final Braille drawing aesthetic and readable.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class StyleInput(BaseModel):
    """Input parameters detailing user style preferences."""
    style_preference: str = Field(default="minimalist", description="Desired style (e.g. minimalist, abstract, high-detail).")
    render_mode: str = Field(default="outline", description="Rendering technique: 'outline' (edges), 'filled' (dithered shading), or 'solid'.")
    density: str = Field(default="medium", description="Density preference: 'low', 'medium', or 'high'.")

class StyleConfig(BaseModel):
    """Aesthetic rendering configs returned by the Style Agent."""
    use_dithering: bool = Field(..., description="Whether to apply dithering algorithms.")
    binarize_threshold: int = Field(..., description="Calculated pixel brightness threshold (0-255).")
    edge_width: int = Field(..., description="Width/thickness of outlines in pixels.")
    cell_mapping_rule: str = Field(..., description="Mapping rule configuration (e.g. light-is-dot, dark-is-dot).")

class StyleOutput(BaseModel):
    """Output configuration payload."""
    config: StyleConfig = Field(..., description="The finalized styling configurations.")
    reasoning: str = Field(..., description="Explanation of why this style configuration was recommended.")
    confidence_score: float = Field(..., description="Confidence score in the style recommendation (0.0 to 1.0).")

class StyleAgent:
    """
    StyleAgent class configuring rendering styles.
    
    System Prompt:
    You are the Style Agent for BrailleArt AI. Your goal is to establish styling rules.
    If the user prefers a minimalist output, recommend clean outline edge detection.
    If they prefer texture, configure Floyd-Steinberg dithering with high density rules.
    """

    def __init__(self, client: Optional[genai.Client] = None):
        """
        Initialize the Style Agent.
        """
        self.client = client or genai.Client()
        self.system_prompt = (
            "You are the Style Agent for BrailleArt AI. Your role is to determine rendering rules, "
            "dithering thresholds, line widths, and fill properties to balance artistic texture "
            "with tactile legibility."
        )

    def determine_style(self, input_data: StyleInput) -> StyleOutput:
        """
        Calculates and recommends aesthetic rendering styling configs.
        
        Args:
            input_data (StyleInput): Style preference selections.
            
        Returns:
            StyleOutput: Configuration rules for the generator.
        """
        # TODO: Process preferences, select best rendering settings using model context
        return StyleOutput(
            config=StyleConfig(
                use_dithering=False,
                binarize_threshold=128,
                edge_width=2,
                cell_mapping_rule="light_is_dot"
            ),
            reasoning="Minimalist outline selection warrants simple edge binarization without dithering noise.",
            confidence_score=0.95
        )

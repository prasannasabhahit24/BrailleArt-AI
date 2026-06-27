"""
learning.py

Learning Agent for BrailleArt AI.
Responsibility:
Personalizes and adapts the output format based on the user's educational profile.
Adjusts Grade 1/2 preferences, language vocabularies, explanation details, 
and narration speed to support classrooms, adults, or therapeutic environments.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class LearningInput(BaseModel):
    """Input defining user profile parameters."""
    user_experience: str = Field(default="beginner", description="User's familiarity with Braille: 'beginner', 'intermediate', or 'advanced'.")
    age_group: str = Field(default="adult", description="User's age group: 'child', 'teen', or 'adult'.")
    educational_setting: Optional[str] = Field(None, description="Context (e.g., 'classroom', 'self-study', 'museum').")

class LearningProfile(BaseModel):
    """Personalization profile configurations."""
    recommended_grade: int = Field(..., description="Recommended Braille grade (1 or 2).")
    explanation_complexity: str = Field(..., description="Vocabulary level: 'simple', 'standard', or 'detailed'.")
    audio_narration_speed: str = Field(..., description="Suggested narration pacing: 'slow', 'medium', or 'fast'.")
    interactive_hints: bool = Field(..., description="Whether to show interactive learning hints in descriptions.")

class LearningOutput(BaseModel):
    """Profile recommendation output payload."""
    profile: LearningProfile = Field(..., description="The calculated user experience profile configs.")
    reasoning: str = Field(..., description="Explanation of why this profile configuration was recommended.")
    confidence_score: float = Field(..., description="Confidence score in educational routing (0.0 to 1.0).")

class LearningAgent:
    """
    LearningAgent class personalizing user outputs.
    
    System Prompt:
    You are the Learning Agent for BrailleArt AI. Your goal is to customize the translation
    and explanation options. Beginners should get Grade 1 Braille and Easy English hints.
    Advanced users should get Grade 2 contracted Braille and technical spatial analysis.
    """

    def __init__(self, client: Optional[genai.Client] = None):
        """
        Initialize the Learning Agent.
        """
        self._client = client
        self.system_prompt = (
            "You are the Learning Agent for BrailleArt AI. Your role is to compute a profile "
            "recommendation to adjust translation grades and narrative complexity to align with "
            "the user's experience and context."
        )

    @property
    def client(self) -> genai.Client:
        """Lazily instantiates the GenAI Client when needed."""
        if self._client is None:
            self._client = genai.Client()
        return self._client

    def personalize_session(self, input_data: LearningInput) -> LearningOutput:
        """
        Generates user profile configurations to customize outputs.
        
        Args:
            input_data (LearningInput): User background factors.
            
        Returns:
            LearningOutput: Adaptability recommendations.
        """
        # TODO: Compute mapping from user experience to profile parameters
        return LearningOutput(
            profile=LearningProfile(
                recommended_grade=1 if input_data.user_experience == "beginner" else 2,
                explanation_complexity="simple" if input_data.age_group == "child" else "standard",
                audio_narration_speed="slow" if input_data.user_experience == "beginner" else "medium",
                interactive_hints=True
            ),
            reasoning="Beginners require uncontracted Grade 1 Braille and slow-paced guidance.",
            confidence_score=0.90
        )

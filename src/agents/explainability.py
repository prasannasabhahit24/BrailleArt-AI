"""
explainability.py

Explainability Agent for BrailleArt AI.
Responsibility:
Updated responsibility.
Explains the reasoning behind each agent's outputs and confidence scores.
Synthesizes an execution report detailing why specific steps were planned, 
how each agent computed its outcomes, and what their respective confidence ratings signify.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class AgentOutcomeLog(BaseModel):
    """Detailed log of an agent's run and confidence score."""
    agent_name: str = Field(..., description="Name of the agent executed.")
    reasoning_summary: str = Field(..., description="Summary explanation of the agent's calculations and choices.")
    confidence_score: float = Field(..., description="The confidence score returned by the agent.")
    confidence_explanation: str = Field(..., description="Explanation of why this confidence level was assigned.")

class ExplainabilityInput(BaseModel):
    """Input payload containing execution records of all agents."""
    session_id: str = Field(..., description="ID of the execution session.")
    outcomes: List[AgentOutcomeLog] = Field(..., description="Outcome records for all executed agents.")
    final_braille_output: str = Field(..., description="The final combined Braille art output.")

class ExplainabilityOutput(BaseModel):
    """Comprehensive explainability report for the user or auditors."""
    audit_report: str = Field(..., description="Detailed text explanation of the multi-agent decision path.")
    confidence_audit_summary: str = Field(..., description="Breakdown of system confidence thresholds and potential weak points.")
    user_friendly_summary: str = Field(..., description="High-level explanation of the system's reasoning for the end-user.")
    confidence_score: float = Field(..., description="Confidence score in the explainability audit (0.0 to 1.0).")

class ExplainabilityAgent:
    """
    ExplainabilityAgent class auditing multi-agent execution.
    
    System Prompt:
    You are the Explainability Agent for BrailleArt AI. Your goal is to review the logs
    and explain the reasoning of all agents. Break down why the planner mapped steps,
    why style/emotion decisions were made, and justify confidence scores so the user
    understands the AI decisions.
    """

    def __init__(self, client: Optional[genai.Client] = None):
        """
        Initialize the Explainability Agent.
        """
        self.client = client or genai.Client()
        self.system_prompt = (
            "You are the Explainability Agent for BrailleArt AI. Your role is to examine agent "
            "log outputs, interpret confidence scores, and write clear explanations of "
            "the system's reasoning at each pipeline phase."
        )

    def generate_explanation(self, input_data: ExplainabilityInput) -> ExplainabilityOutput:
        """
        Synthesizes execution logs and writes an explainability report.
        
        Args:
            input_data (ExplainabilityInput): Execution outputs and logs.
            
        Returns:
            ExplainabilityOutput: Unified explanation report.
        """
        # TODO: Send outcomes to Gemini 2.5 Flash to write structured audit explanations
        return ExplainabilityOutput(
            audit_report="Audit Report: All steps executed in sequence. SecurityAgent verified input safety (confidence 1.0). VisionAgent identified circular boundaries (confidence 0.90).",
            confidence_audit_summary="Average system confidence is 0.95. All sub-agents exceeded the 0.80 validation threshold.",
            user_friendly_summary="The system processed your image by validating its safety, mapping its outlines, and rendering the dots to match standard Braille formats.",
            confidence_score=0.98
        )

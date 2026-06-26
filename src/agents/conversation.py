"""
conversation.py

Conversation Agent for BrailleArt AI.
Responsibility:
Manages interactive natural language dialogue with the user.
Clarifies requirements, explains how to use the generator, fields questions, 
and translates conversational requests (e.g., 'make the borders thicker') 
into structured configuration tweaks for the orchestrator.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class ChatMessage(BaseModel):
    """A single message in the chat history."""
    role: str = Field(..., description="The sender's role: 'user' or 'assistant'.")
    content: str = Field(..., description="Text content of the message.")

class ConversationInput(BaseModel):
    """Input payload containing chat message and history."""
    message: str = Field(..., description="The new user chat message.")
    history: List[ChatMessage] = Field(default_factory=list, description="Historical chat messages in the current session.")
    current_state: Dict[str, Any] = Field(default_factory=dict, description="Current application state (active image name, style, etc.).")

class ConversationOutput(BaseModel):
    """The conversational response and suggested state changes."""
    response: str = Field(..., description="The assistant's natural language reply.")
    state_updates: Dict[str, Any] = Field(default_factory=dict, description="Requested parameters to change (e.g. threshold=140).")
    suggested_followups: List[str] = Field(default_factory=list, description="Buttons or quick replies to show in the UI.")
    confidence_score: float = Field(..., description="Model confidence in dialog alignment (0.0 to 1.0).")

class ConversationAgent:
    """
    ConversationAgent class managing user dialogues.
    
    System Prompt:
    You are the Conversation Agent for BrailleArt AI. Your goal is to guide the user in
    creating tactile designs. Answer questions, suggest inputs, and listen to natural
    language style instructions to parse parameter overrides for the backend.
    """

    def __init__(self, client: Optional[genai.Client] = None):
        """
        Initialize the Conversation Agent.
        """
        self.client = client or genai.Client()
        self.system_prompt = (
            "You are the Conversation Agent for BrailleArt AI. Your role is to interact with users, "
            "provide assistance, clarify complex shapes, and extract configuration tweaks "
            "from descriptive chat commands."
        )

    def process_message(self, input_data: ConversationInput) -> ConversationOutput:
        """
        Processes conversational messages and determines text replies and state updates.
        
        Args:
            input_data (ConversationInput): Current message and chat logs.
            
        Returns:
            ConversationOutput: Response text and param updates.
        """
        # TODO: Send messages and system context to Gemini 2.5 Flash
        return ConversationOutput(
            response="I can help you convert that image. I've adjusted the threshold to edge outlines.",
            state_updates={"render_mode": "outline"},
            suggested_followups=["Explain this art", "Show similar art", "Check accessibility"],
            confidence_score=0.98
        )

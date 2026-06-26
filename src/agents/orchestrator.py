"""
orchestrator.py

Orchestrator Agent for BrailleArt AI.
Responsibility:
Accepts the Planner Agent's output (execution plan), maps agent names to classes,
sequentially runs each agent step with stopwatch timers, shares context, 
and aggregates traces (success/failure, timing, errors).
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from dotenv import load_dotenv

# Import all agents and their input models
from .planner import PlannerOutput
from .security import SecurityAgent, SecurityInput
from .learning import LearningAgent, LearningInput
from .vision import VisionAgent, VisionInput
from .ocr import OCRAgent, OCRInput
from .style import StyleAgent, StyleInput
from .emotion import EmotionAgent, EmotionInput
from .art_knowledge import ArtKnowledgeAgent, ArtKnowledgeInput
from .tactile import TactileAgent, TactileInput
from .braille import BrailleAgent, BrailleInput
from .conversation import ConversationAgent, ConversationInput
from .reflection import ReflectionAgent, ReflectionInput
from .accessibility import AccessibilityAgent, AccessibilityInput
from .explainability import ExplainabilityAgent, ExplainabilityInput, AgentOutcomeLog
from .evaluation import EvaluationAgent, EvaluationInput

# Initialize logging
logger = logging.getLogger("brailleart_ai.orchestrator")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Load environment variables
load_dotenv()

class TraceEntry(BaseModel):
    """Execution statistics for an individual agent in the trace log."""
    agent: str = Field(..., description="The name identifier of the agent.")
    status: str = Field(..., description="Status of execution: 'completed', 'failed', or 'skipped'.")
    execution_time_ms: int = Field(..., description="Time elapsed during the agent run in milliseconds.")
    error_message: Optional[str] = Field(default=None, description="Detailed error description if execution failed.")

class SharedContext(BaseModel):
    """The central state registry shared between sequential agents."""
    user_prompt: str = Field(..., description="The raw initial query from the user.")
    has_image: bool = Field(default=False, description="Flag indicating if image data is present.")
    raw_image_bytes: Optional[bytes] = Field(default=None, description="The binarized or sanitized image binary payload.")
    image_metadata: Dict[str, Any] = Field(default_factory=dict, description="File details like size, format, name.")
    session_id: str = Field(default="session-uuid-default", description="Active session ID tracker.")
    
    # Cumulative execution outputs stored as dictionary dumps of Pydantic schemas
    security: Optional[Dict[str, Any]] = None
    learning: Optional[Dict[str, Any]] = None
    vision: Optional[Dict[str, Any]] = None
    ocr: Optional[Dict[str, Any]] = None
    style: Optional[Dict[str, Any]] = None
    emotion: Optional[Dict[str, Any]] = None
    art_knowledge: Optional[Dict[str, Any]] = None
    tactile: Optional[Dict[str, Any]] = None
    braille: Optional[Dict[str, Any]] = None
    conversation: Optional[Dict[str, Any]] = None
    reflection: Optional[Dict[str, Any]] = None
    accessibility: Optional[Dict[str, Any]] = None
    explainability: Optional[Dict[str, Any]] = None
    evaluation: Optional[Dict[str, Any]] = None

class OrchestratorResponse(BaseModel):
    """Final summary of the pipeline orchestration session."""
    trace: List[TraceEntry] = Field(..., description="Sequential log trace of executed agent operations.")
    shared_context: Dict[str, Any] = Field(..., description="Final dump of the SharedContext state.")
    final_output: str = Field(..., description="The main generated Braille art or core textual output.")
    success: bool = Field(..., description="Flag indicating if the critical path executed successfully.")

# List of critical agents that block execution if they fail
CRITICAL_AGENTS = {"security", "vision", "tactile"}

class OrchestratorAgent:
    """
    Orchestrator Agent class that sequentially directs data between sub-agents,
    catches and logs errors, and returns a detailed execution timeline trace.
    """

    def __init__(self, client: Optional[genai.Client] = None):
        """
        Initializes the Orchestrator with an optional pre-configured Gemini client.
        """
        self._client = client

    @property
    def client(self) -> genai.Client:
        """Lazily instantiates the GenAI Client when needed."""
        if self._client is None:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY is not defined in the environment. Client calls will fail.")
            self._client = genai.Client()
        return self._client

    async def execute_plan(
        self, 
        plan: PlannerOutput, 
        initial_prompt: str, 
        image_bytes: Optional[bytes] = None, 
        image_meta: Optional[Dict[str, Any]] = None
    ) -> OrchestratorResponse:
        """
        Runs the planned agent sequence sequentially, compiling shared context state.
        
        Args:
            plan (PlannerOutput): Plan detailing which agents to execute.
            initial_prompt (str): Text description or user request.
            image_bytes (bytes, optional): Image payload data.
            image_meta (dict, optional): Upload metadata dictionary.
            
        Returns:
            OrchestratorResponse: Pipeline audit trace and aggregated output state.
        """
        logger.info(f"Orchestration pipeline execution started. Total steps in plan: {len(plan.execution_plan)}")

        # Initialize shared context state
        context = SharedContext(
            user_prompt=initial_prompt,
            has_image=(image_bytes is not None),
            raw_image_bytes=image_bytes,
            image_metadata=image_meta or {}
        )

        trace: List[TraceEntry] = []
        pipeline_success = True

        for agent_name in plan.execution_plan:
            agent_id = agent_name.lower().strip()
            logger.info(f"Running agent: [{agent_id}]")
            
            start_time = time.perf_counter()
            status = "completed"
            error_msg = None

            try:
                # Dispatch execution logic to the corresponding sub-agent method
                await self._execute_agent_step(agent_id, context)
                logger.info(f"Agent [{agent_id}] completed successfully.")

            except Exception as exc:
                logger.exception(f"Unhandled exception during execution of non-critical agent [{agent_id}]: {exc}")
                status = "failed"
                error_msg = str(exc)

                # Check if this agent failure is non-tolerable
                if agent_id in CRITICAL_AGENTS:
                    logger.error(f"Critical agent failure in [{agent_id}]. Aborting pipeline.")
                    pipeline_success = False
                    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                    trace.append(TraceEntry(
                        agent=agent_name,
                        status=status,
                        execution_time_ms=elapsed_ms,
                        error_message=f"CRITICAL ERROR: {error_msg}"
                    ))
                    break

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            trace.append(TraceEntry(
                agent=agent_name,
                status=status,
                execution_time_ms=elapsed_ms,
                error_message=error_msg
            ))

        # Synthesize final output. Prioritize tactile grid, fallback to conversation or translation.
        final_out = "No Braille output generated."
        if context.tactile and "braille_grid" in context.tactile:
            final_out = context.tactile["braille_grid"]
        elif context.braille and "translated_braille" in context.braille:
            final_out = context.braille["translated_braille"]
        elif context.conversation and "response" in context.conversation:
            final_out = context.conversation["response"]

        # Prepare final context dictionary, excluding raw file bytes to save bandwidth in API traces
        context_dump = context.model_dump()
        if "raw_image_bytes" in context_dump:
            context_dump["raw_image_bytes"] = None

        return OrchestratorResponse(
            trace=trace,
            shared_context=context_dump,
            final_output=final_out,
            success=pipeline_success
        )

    @property
    def safe_client(self) -> Optional[genai.Client]:
        """Returns the client if GEMINI_API_KEY is configured, else None."""
        if os.getenv("GEMINI_API_KEY"):
            return self.client
        return None

    async def _execute_agent_step(self, agent_id: str, context: SharedContext) -> None:
        """
        Initializes and runs the target agent, pulling parameters from shared context,
        and merging the resulting schema dump back into context state.
        
        Args:
            agent_id (str): Lowercase identifier matching the file names.
            context (SharedContext): Read/Write shared state object.
        """
        # Dynamic Dispatch Logic
        if agent_id == "security":
            agent = SecurityAgent(client=self.safe_client)
            inp = SecurityInput(
                filename=context.image_metadata.get("filename", "upload.png"),
                file_data=context.raw_image_bytes or b"",
                claimed_mime_type=context.image_metadata.get("claimed_mime_type", "image/png"),
                max_size_bytes=context.image_metadata.get("max_size_bytes", 10 * 1024 * 1024)
            )
            out, sanitized_bytes = agent.validate_and_sanitize(inp)
            context.security = out.model_dump()
            if not out.is_safe:
                raise ValueError(f"Security validation failed: {out.error_message or 'Unsafe payload detected.'}")
            context.raw_image_bytes = sanitized_bytes

        elif agent_id == "learning":
            agent = LearningAgent(client=self.safe_client)
            inp = LearningInput(
                user_experience=context.image_metadata.get("user_experience", "beginner"),
                age_group=context.image_metadata.get("age_group", "adult"),
                educational_setting=context.image_metadata.get("educational_setting", "self-study")
            )
            out = agent.personalize_session(inp)
            context.learning = out.model_dump()

        elif agent_id == "vision":
            agent = VisionAgent(client=self.safe_client)
            inp = VisionInput(
                image_bytes=context.raw_image_bytes or b"",
                focus_areas=context.image_metadata.get("focus_areas", None)
            )
            out = agent.analyze_image(inp)
            context.vision = out.model_dump()

        elif agent_id == "ocr":
            agent = OCRAgent(client=self.safe_client)
            inp = OCRInput(image_bytes=context.raw_image_bytes or b"")
            out = agent.extract_text(inp)
            context.ocr = out.model_dump()

        elif agent_id == "style":
            agent = StyleAgent(client=self.safe_client)
            # Extract recommendations from learning/vision to adjust style decisions
            pref = context.image_metadata.get("style_preference", "minimalist")
            mode = "outline"
            if context.learning and context.learning.get("profile"):
                if context.learning["profile"].get("explanation_complexity") == "detailed":
                    pref = "high-detail"
            inp = StyleInput(
                style_preference=pref,
                render_mode=mode,
                density=context.image_metadata.get("density", "medium")
            )
            out = agent.determine_style(inp)
            context.style = out.model_dump()

        elif agent_id == "emotion":
            agent = EmotionAgent(client=self.safe_client)
            inp = EmotionInput(
                user_prompt=context.user_prompt,
                visual_description=context.vision.get("spatial_layout_description") if context.vision else None
            )
            out = agent.analyze_emotion(inp)
            context.emotion = out.model_dump()

        elif agent_id == "art_knowledge":
            agent = ArtKnowledgeAgent(client=self.safe_client)
            inp = ArtKnowledgeInput(
                image_bytes=context.raw_image_bytes,
                artwork_description=context.user_prompt
            )
            out = agent.identify_artwork(inp)
            context.art_knowledge = out.model_dump()

        elif agent_id == "tactile":
            agent = TactileAgent(client=self.safe_client)
            # Create a simple mock grid since tools/braille_tool image convert is not integrated yet
            w = 80
            h = 24
            if context.style and context.style.get("config"):
                w = context.image_metadata.get("char_width", 80)
            inp = TactileInput(
                binary_grid=[[0] * w for _ in range(h)],
                char_width=w,
                char_height=h
            )
            out = agent.generate_tactile_layout(inp)
            context.tactile = out.model_dump()

        elif agent_id == "braille":
            agent = BrailleAgent(client=self.safe_client)
            # Use OCR text if found, else default to translating the user prompt
            text = context.user_prompt
            if context.ocr and context.ocr.get("combined_text"):
                text = context.ocr["combined_text"]
            
            grade = 1
            if context.learning and context.learning.get("profile"):
                grade = context.learning["profile"].get("recommended_grade", 1)

            inp = BrailleInput(
                source_text=text,
                braille_grade=grade,
                uppercase_indicators=True
            )
            out = agent.translate(inp)
            context.braille = out.model_dump()

        elif agent_id == "conversation":
            agent = ConversationAgent(client=self.safe_client)
            inp = ConversationInput(
                message=context.user_prompt,
                history=[],
                current_state={}
            )
            out = agent.process_message(inp)
            context.conversation = out.model_dump()

        elif agent_id == "reflection":
            agent = ReflectionAgent(client=self.safe_client)
            inp = ReflectionInput(
                braille_output=context.tactile.get("braille_grid") if context.tactile else "",
                source_context=context.user_prompt,
                iteration=1
            )
            out = agent.critique_draft(inp)
            context.reflection = out.model_dump()

        elif agent_id == "accessibility":
            agent = AccessibilityAgent(client=self.safe_client)
            inp = AccessibilityInput(
                braille_output=context.tactile.get("braille_grid") if context.tactile else "",
                text_context=context.user_prompt,
                has_audio_enabled=True
            )
            out = agent.generate_accessibility_pack(inp)
            context.accessibility = out.model_dump()

        elif agent_id == "explainability":
            agent = ExplainabilityAgent(client=self.safe_client)
            # Package outcome logs containing sub-agent reasoning summaries & confidence values
            logs = []
            for item in ["security", "learning", "vision", "ocr", "style", "emotion", "art_knowledge", "tactile", "braille"]:
                field = getattr(context, item, None)
                if field and isinstance(field, dict):
                    logs.append(AgentOutcomeLog(
                        agent_name=item.capitalize(),
                        reasoning_summary=field.get("reasoning", field.get("spatial_layout_description", "Completed")),
                        confidence_score=field.get("confidence_score", 1.0),
                        confidence_explanation="Score computed during execution evaluation."
                    ))

            inp = ExplainabilityInput(
                session_id=context.session_id,
                outcomes=logs,
                final_braille_output=context.tactile.get("braille_grid") if context.tactile else ""
            )
            out = agent.generate_explanation(inp)
            context.explainability = out.model_dump()

        elif agent_id == "evaluation":
            agent = EvaluationAgent(client=self.safe_client)
            inp = EvaluationInput(
                original_image_bytes=context.raw_image_bytes,
                original_prompt=context.user_prompt,
                generated_braille=context.tactile.get("braille_grid") if context.tactile else ""
            )
            out = agent.evaluate_output(inp)
            context.evaluation = out.model_dump()

        else:
            logger.warning(f"Attempted to run unknown agent: [{agent_id}]. Skipping step.")

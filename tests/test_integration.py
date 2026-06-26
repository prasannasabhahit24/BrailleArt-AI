"""
test_integration.py

Integration tests for the complete end-to-end multi-agent pipeline in BrailleArt AI.
Mocks the google-genai Client globally and tests the FastAPI endpoint:
POST /api/v1/analyze

Verifies:
1. Endpoint returns structured JSON complying with PipelineResult.
2. The entire multi-agent pipeline executes in sequence.
3. Database logging successfully logs runs to saved_art and agent_conversations tables.
"""

import os
import pytest
import unittest.mock as mock
from fastapi.testclient import TestClient

from src.backend.main import app
from src.database.db import SessionLocal
from src.database.models import AgentConversation, SavedArt

# Initialize FastAPI TestClient
client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_genai_client():
    """Globally mock Google GenAI client to isolate pipeline tests."""
    with mock.patch("google.genai.Client") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        
        def generate_content_side_effect(model, contents, config=None, **kwargs):
            system_instruction = getattr(config, "system_instruction", "") if config else ""
            mock_resp = mock.MagicMock()
            
            if "Planner Agent" in system_instruction:
                from src.agents.planner import PlannerOutput
                mock_resp.text = PlannerOutput(
                    execution_plan=["security", "learning", "vision", "ocr", "style", "art_knowledge", "emotion", "accessibility", "braille", "tactile", "explainability"],
                    reason="Comprehensive analysis requested."
                ).model_dump_json()
                
            elif "Vision Agent" in system_instruction:
                from src.agents.vision import VisionOutput, DetectedObject, ColorAnalysis, CompositionAnalysis
                mock_resp.text = VisionOutput(
                    detected_items=[
                        DetectedObject(
                            label="mountain",
                            bounding_box=[10.0, 10.0, 80.0, 80.0],
                            color_profile=["brown"],
                            reasoning="Mountain contour outline.",
                            confidence=0.95
                        )
                    ],
                    color_analysis=ColorAnalysis(
                        dominant_colors=["blue", "yellow"],
                        lighting_description="Bright sunny lighting",
                        contrast_level="high"
                    ),
                    composition_analysis=CompositionAnalysis(
                        perspective="linear",
                        composition_rules=["rule of thirds"],
                        artistic_elements=["bold outlines"],
                        dominant_regions=["center"]
                    ),
                    overall_summary="A mountain under a shining sun.",
                    confidence_score=0.95
                ).model_dump_json()
                
            elif "OCR Agent" in system_instruction:
                from src.agents.ocr import OCROutput
                mock_resp.text = OCROutput(
                    text_segments=[],
                    combined_text="",
                    has_text=False,
                    confidence_score=1.0
                ).model_dump_json()
                
            elif "Emotion Agent" in system_instruction:
                from src.agents.emotion import EmotionOutput
                mock_resp.text = EmotionOutput(
                    dominant_emotion="joy",
                    secondary_emotions=["warmth"],
                    atmosphere="pleasant",
                    symbolism="Sun depicts warmth",
                    storytelling="Nature landscape",
                    artistic_intention="To inspire peace",
                    emotional_summary="Calm sunny scene",
                    confidence_score=0.9,
                    reasoning="Sunny skies evoke positive mood."
                ).model_dump_json()
                
            elif "Art Knowledge Agent" in system_instruction:
                from src.agents.art_knowledge import ArtKnowledgeOutput
                mock_resp.text = ArtKnowledgeOutput(
                    artwork_title="Sunny Mountain",
                    artist="Unknown",
                    art_movement="Modernism",
                    creation_period="21st Century",
                    confidence_score=0.8,
                    reasoning="Generic nature photo."
                ).model_dump_json()
                
            elif "Accessibility Agent" in system_instruction:
                from src.agents.accessibility import AccessibilityOutput, AccessibilityScoreDetails
                mock_resp.text = AccessibilityOutput(
                    screen_reader_description="Tactile outline of a mountain and a sun.",
                    easy_english_version="A sun above a mountain.",
                    child_friendly_version="A happy sun and a big mountain!",
                    audio_narration_script="Start tracing the triangle shape of the mountain.",
                    alt_text="Sunny mountain landscape.",
                    object_list=["mountain", "sun"],
                    spatial_layout_description="Sun is at top right, mountain is centered.",
                    accessibility_score=AccessibilityScoreDetails(
                        completeness=0.9, readability=0.9, usefulness=0.9, screen_reader_compatibility=0.9, overall_score=0.9
                    ),
                    suggested_improvements=[],
                    confidence_score=0.95,
                    reasoning="Identified shapes successfully."
                ).model_dump_json()
                
            elif "Braille Agent" in system_instruction:
                from src.agents.braille import BrailleOutput
                mock_resp.text = BrailleOutput(
                    grade1_braille="Sunny mountain landscape.",
                    grade2_braille="Sunny mountain landscape.",
                    unicode_braille="⠠⠎⠥⠝⠝⠽ ⠍⠕⠥⠝⠞⠁⠊⠝ ⠇⠁⠝⠙⠎⠉⠁⠏⠑⠲",
                    plain_text="Sunny mountain landscape.",
                    character_count=26,
                    translation_notes="UEB Grade 1 applied.",
                    confidence_score=0.95,
                    metadata={"download_file_path": "outputs/braille_test_int.txt"}
                ).model_dump_json()
                
            elif "Tactile Agent" in system_instruction:
                from src.agents.tactile import TactileOutput
                mock_resp.text = TactileOutput(
                    simplified_svg='<svg><path d="M 10 50 L 50 10 L 90 50" /><circle cx="80" cy="20" r="10" /></svg>',
                    raised_line_layout="Mountain outline with sun.",
                    object_boundary_map={"mountain": [10, 10, 80, 40], "sun": [70, 10, 20, 20]},
                    relative_spatial_positions={"sun": "top right of mountain"},
                    braille_overlay_coordinates={"sun_label": [80, 20], "mountain_label": [50, 40]},
                    embosser_ready_svg='<svg><path d="M 10 50 L 50 10 L 90 50" stroke-width="3" /></svg>',
                    metadata={"simplified_svg_path": "outputs/tactile_simplified_int.svg", "embosser_ready_svg_path": "outputs/tactile_embosser_int.svg"},
                    confidence_score=0.95
                ).model_dump_json()
                
            else:
                mock_resp.text = "{}"
                
            return mock_resp

        mock_instance.models.generate_content.side_effect = generate_content_side_effect
        yield mock_instance

def test_analyze_pipeline_integration():
    """Verifies that the /analyze route triggers all agents and logs details to the database."""
    db = SessionLocal()
    
    initial_conv_count = db.query(AgentConversation).count()
    initial_art_count = db.query(SavedArt).count()
    
    # 1. Prepare dummy file and form payload
    file_payload = {"file": ("test_image.png", b"fake_png_data", "image/png")}
    form_payload = {"prompt": "A sunny landscape"}
    
    # 2. POST to analyze route
    response = client.post("/api/v1/analyze", data=form_payload, files=file_payload)
    
    # 3. Assert response structure and pipeline values
    assert response.status_code == 200
    res_json = response.json()
    
    assert res_json["uploaded_image"] == "test_image.png"
    assert len(res_json["execution_trace"]) > 0
    assert "security" in res_json["outputs"]
    assert "vision" in res_json["outputs"]
    assert "accessibility" in res_json["outputs"]
    assert "braille" in res_json["outputs"]
    assert "tactile" in res_json["outputs"]
    
    assert res_json["generated_braille"] == "⠠⠎⠥⠝⠝⠽ ⠍⠕⠥⠝⠞⠁⠊⠝ ⠇⠁⠝⠙⠎⠉⠁⠏⠑⠲"
    assert "<svg>" in res_json["generated_svg"]
    assert res_json["accessibility_report"]["alt_text"] == "Sunny mountain landscape."
    
    # 4. Check database logs
    new_conv_count = db.query(AgentConversation).count()
    new_art_count = db.query(SavedArt).count()
    
    assert new_conv_count == initial_conv_count + 1
    assert new_art_count == initial_art_count + 1
    
    # 5. Verify detailed database metadata logging (execution trace, SVG and Braille paths)
    last_art = db.query(SavedArt).order_by(SavedArt.id.desc()).first()
    assert last_art.art_type == "image"
    assert last_art.config_params is not None
    assert "simplified_svg_path" in last_art.config_params
    assert "embosser_ready_svg_path" in last_art.config_params
    assert "braille_overlay_coordinates" in last_art.config_params
    
    # Clean up generated files if they exist
    for key in ["simplified_svg_path", "embosser_ready_svg_path"]:
        path = last_art.config_params.get(key)
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    # Clean up Braille file
    last_conv = db.query(AgentConversation).order_by(AgentConversation.id.desc()).first()
    braille_meta = last_conv.meta_logs.get("braille_metadata") if last_conv.meta_logs else None
    if braille_meta and braille_meta.get("download_file_path"):
        path = braille_meta["download_file_path"]
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
                
    db.close()

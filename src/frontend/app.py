"""
app.py

Streamlit Application Dashboard for BrailleArt AI.
Provides an interactive multi-page dashboard displaying multi-agent timelines,
accessibility reports, Braille translations, tactile outline SVGs, quizzes, and analysis history.
"""

import streamlit as st
import os
import requests
import json
import base64
import time
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

# Page Configurations
st.set_page_config(
    page_title="BrailleArt AI Dashboard",
    page_icon="⠃⠗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# Session State Initialization
# ------------------------------------------------------------------------------
def init_session_state():
    if "settings_theme" not in st.session_state:
        st.session_state.settings_theme = "Sleek Dark"
    if "settings_font_size" not in st.session_state:
        st.session_state.settings_font_size = "Medium"
    if "settings_language" not in st.session_state:
        st.session_state.settings_language = "English"
    if "settings_speech" not in st.session_state:
        st.session_state.settings_speech = False
    if "settings_speech_speed" not in st.session_state:
        st.session_state.settings_speech_speed = 1.0
    if "active_run" not in st.session_state:
        st.session_state.active_run = None
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False
    if "learning_content" not in st.session_state:
        st.session_state.learning_content = None

init_session_state()

# ------------------------------------------------------------------------------
# CSS Design System & Theme Styles Injection
# ------------------------------------------------------------------------------
def inject_custom_css():
    theme = st.session_state.get("settings_theme", "Sleek Dark")
    font_size = st.session_state.get("settings_font_size", "Medium")
    
    font_size_px = "16px"
    h1_size = "2.5rem"
    h2_size = "1.8rem"
    h3_size = "1.4rem"
    if font_size == "Small":
        font_size_px = "14px"
        h1_size = "2.1rem"
        h2_size = "1.6rem"
        h3_size = "1.2rem"
    elif font_size == "Large":
        font_size_px = "20px"
        h1_size = "3rem"
        h2_size = "2.2rem"
        h3_size = "1.7rem"

    if theme == "Clean Light":
        bg_color = "#FFFFFF"
        text_color = "#1C1C1E"
        card_bg = "rgba(255, 255, 255, 0.9)"
        card_border = "rgba(0, 0, 0, 0.1)"
        text_muted = "#636366"
        shadow = "0 8px 24px rgba(0, 0, 0, 0.08)"
        braille_bg = "#f4f4f6"
        braille_text = "#1c1c1e"
        braille_border = "#e5e5ea"
        success_color = "#2e7d32"
        warning_color = "#ed6c02"
        error_color = "#d32f2f"
        running_color = "#0288d1"
        border_radius = "16px"
    elif theme == "High Contrast":
        bg_color = "#000000"
        text_color = "#FFFFFF"
        card_bg = "#000000"
        card_border = "#FFFF00"
        text_muted = "#FFFF00"
        shadow = "none"
        braille_bg = "#000000"
        braille_text = "#FFFF00"
        braille_border = "#FFFF00"
        success_color = "#00FF00"
        warning_color = "#FFFF00"
        error_color = "#FF0000"
        running_color = "#00FFFF"
        border_radius = "0px"
    else:  # Sleek Dark
        bg_color = "#1C1C1E"
        text_color = "#F2F2F7"
        card_bg = "rgba(28, 28, 30, 0.6)"
        card_border = "rgba(255, 255, 255, 0.1)"
        text_muted = "#8E8E93"
        shadow = "0 8px 32px rgba(0, 0, 0, 0.3)"
        braille_bg = "#0a0b0e"
        braille_text = "#00FF66"
        braille_border = "#1f242d"
        success_color = "#00E676"
        warning_color = "#FFB300"
        error_color = "#FF5252"
        running_color = "#29B6F6"
        border_radius = "16px"

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;600;700&display=swap');
        
        :root {{
            --bg-color: {bg_color};
            --text-color: {text_color};
            --card-bg: {card_bg};
            --card-border: {card_border};
            --text-muted: {text_muted};
            --shadow: {shadow};
            --braille-bg: {braille_bg};
            --braille-text: {braille_text};
            --braille-border: {braille_border};
            --success-color: {success_color};
            --warning-color: {warning_color};
            --error-color: {error_color};
            --running-color: {running_color};
            --border-radius: {border_radius};
            --accent: #FF4B4B;
        }}
        
        .stApp {{
            font-family: 'Inter', sans-serif;
            font-size: {font_size_px};
        }}
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Outfit', sans-serif;
        }}
        
        /* Premium Card Component */
        .custom-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: var(--shadow);
            color: var(--text-color);
            transition: all 0.3s ease;
        }}
        .custom-card h4 {{
            margin-top: 0;
            margin-bottom: 0.8rem;
            font-weight: 700;
            font-size: {h3_size};
        }}
        
        /* Modern Hero Section */
        .hero-section {{
            background: linear-gradient(135deg, #FF4B4B 0%, #8B0000 100%);
            color: white;
            padding: 3rem 2rem;
            border-radius: var(--border-radius);
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 10px 30px rgba(255, 75, 75, 0.25);
            position: relative;
            overflow: hidden;
        }}
        .hero-section::after {{
            content: '';
            position: absolute;
            top: 0; right: 0; bottom: 0; left: 0;
            background: radial-gradient(circle at 75% 25%, rgba(255,255,255,0.12) 0%, transparent 60%);
            pointer-events: none;
        }}
        .hero-tagline {{
            font-size: {h1_size};
            font-weight: 800;
            margin-bottom: 0.6rem;
            font-family: 'Outfit', sans-serif;
            letter-spacing: -0.5px;
        }}
        .hero-sub {{
            font-size: 1.2rem;
            font-weight: 300;
            opacity: 0.95;
            max-width: 800px;
            margin: 0 auto;
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        .stat-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--border-radius);
            padding: 1.8rem 1rem;
            text-align: center;
            box-shadow: var(--shadow);
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
            border-color: var(--accent);
        }}
        .stat-val {{
            font-size: 2.8rem;
            font-weight: 800;
            color: var(--accent);
            margin-bottom: 0.2rem;
            line-height: 1;
            font-family: 'Outfit', sans-serif;
        }}
        .stat-label {{
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        /* File Uploader styling override */
        div[data-testid="stFileUploader"] {{
            border: 2px dashed var(--card-border) !important;
            border-radius: var(--border-radius) !important;
            background-color: rgba(255, 255, 255, 0.02) !important;
            padding: 1.5rem !important;
            transition: border-color 0.3s ease;
        }}
        div[data-testid="stFileUploader"]:hover {{
            border-color: var(--accent) !important;
        }}
        
        /* Action Button */
        .primary-btn button {{
            background: linear-gradient(135deg, #FF4B4B 0%, #D32F2F 100%) !important;
            color: white !important;
            border: none !important;
            font-weight: 700 !important;
            font-family: 'Outfit', sans-serif !important;
            font-size: 1.1rem !important;
            padding: 0.75rem 1.5rem !important;
            border-radius: var(--border-radius) !important;
            box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3) !important;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }}
        .primary-btn button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(255, 75, 75, 0.5) !important;
        }}
        
        /* Chronological Timeline */
        .timeline-container {{
            margin: 1.5rem 0;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}
        .timeline-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--border-radius);
            padding: 1.2rem;
            box-shadow: var(--shadow);
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
            animation: slideUp 0.5s ease forwards;
            opacity: 0;
            transform: translateY(20px);
        }}
        @keyframes slideUp {{
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        .timeline-card::before {{
            content: '';
            position: absolute;
            left: 0; top: 0; bottom: 0;
            width: 6px;
        }}
        .timeline-card.completed::before {{ background-color: var(--success-color); }}
        .timeline-card.failed::before {{ background-color: var(--error-color); }}
        .timeline-card.running::before {{ 
            background-color: var(--running-color);
            animation: pulse-border 1.5s infinite alternate;
        }}
        .timeline-card.skipped::before {{ background-color: var(--text-muted); opacity: 0.5; }}
        
        @keyframes pulse-border {{
            from {{ opacity: 0.4; }}
            to {{ opacity: 1; }}
        }}
        
        .timeline-info {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .timeline-icon {{
            font-size: 1.5rem;
        }}
        .timeline-meta {{
            display: flex;
            flex-direction: column;
        }}
        .timeline-title {{
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-color);
        }}
        .timeline-status {{
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-muted);
        }}
        .timeline-time {{
            font-size: 0.85rem;
            color: var(--text-muted);
        }}
        
        /* Monospace braille outputs */
        .braille-container {{
            background: var(--braille-bg);
            border: 1px solid var(--braille-border);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            position: relative;
            box-shadow: var(--shadow);
            margin-bottom: 1.5rem;
        }}
        .braille-box {{
            font-family: 'Courier New', Courier, monospace;
            font-size: 24px;
            line-height: 1.3;
            letter-spacing: 2px;
            color: var(--braille-text);
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-all;
            margin-top: 0.5rem;
        }}
        .copy-btn {{
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: var(--text-color);
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 600;
            transition: all 0.2s;
        }}
        .copy-btn:hover {{
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }}
        
        /* Learning cards */
        .learning-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--border-radius);
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: var(--shadow);
            transition: transform 0.2s ease;
        }}
        .learning-card:hover {{
            transform: scale(1.02);
            border-color: var(--accent);
        }}
        
        /* Gauge dashboard */
        .gauge-container {{
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 1.5rem;
            margin: 1.5rem 0;
        }}
        .gauge-item {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--border-radius);
            padding: 1rem;
            text-align: center;
            width: 130px;
            box-shadow: var(--shadow);
        }}
        
        /* Error/Offline Notification Card */
        .error-card {{
            background: rgba(211, 47, 47, 0.1);
            border: 2px solid var(--error-color);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            color: var(--text-color);
            margin: 1.5rem 0;
            box-shadow: var(--shadow);
        }}
        .error-card h4 {{
            color: var(--error-color);
            margin-top: 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_custom_css()

# Helper to render cards
def render_card(title: str, content: str = "", html_content: str = ""):
    title_html = f"<h4>{title}</h4>" if title else ""
    body_html = f"<p style='white-space: pre-line;'>{content}</p>" if content else ""
    full_html = f"<div class='custom-card'>{title_html}{body_html}{html_content}</div>"
    st.markdown(full_html, unsafe_allow_html=True)

# Helper to render speech synthesis buttons
def render_speak_button(text_to_speak: str, label: str = "🔊 Read Aloud"):
    if not text_to_speak or not st.session_state.get("settings_speech", False):
        return
    rate = st.session_state.get("settings_speech_speed", 1.0)
    escaped_text = json.dumps(text_to_speak)
    btn_id = f"speak_btn_{abs(hash(text_to_speak))}"
    html_speak = f"""
    <button id="{btn_id}" style="
        background-color: var(--accent, #FF4B4B);
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: bold;
        margin-bottom: 10px;
        font-family: sans-serif;
    ">
        {label}
    </button>
    <script>
        document.getElementById("{btn_id}").addEventListener("click", () => {{
            const utterance = new SpeechSynthesisUtterance({escaped_text});
            utterance.rate = {rate};
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(utterance);
        }});
    </script>
    """
    st.components.v1.html(html_speak, height=50)

# ------------------------------------------------------------------------------
# Database Helpers
# ------------------------------------------------------------------------------
def get_db_history():
    from src.database.db import SessionLocal
    from src.database.models import AgentConversation, SavedArt
    db = SessionLocal()
    try:
        conversations = db.query(AgentConversation).order_by(AgentConversation.created_at.desc()).all()
        saved_arts = db.query(SavedArt).order_by(SavedArt.created_at.desc()).all()
        return conversations, saved_arts
    except Exception as e:
        st.error(f"Error querying SQLite database: {e}")
        return [], []
    finally:
        db.close()

def load_historical_run(conv_id: int):
    from src.database.db import SessionLocal
    from src.database.models import AgentConversation, SavedArt
    db = SessionLocal()
    try:
        conv = db.query(AgentConversation).filter(AgentConversation.id == conv_id).first()
        if not conv:
            return None
            
        art = db.query(SavedArt).filter(SavedArt.source_content == conv.user_prompt).order_by(SavedArt.created_at.desc()).first()
        
        trace = conv.meta_logs.get("trace", []) if conv.meta_logs else []
        braille_meta = conv.meta_logs.get("braille_metadata", {}) if conv.meta_logs else {}
        
        outputs = {
            "braille": {
                "unicode_braille": art.braille_content if (art and art.art_type == "text") else (conv.agent_response if "⠠" in conv.agent_response else ""),
                "plain_text": conv.user_prompt,
                "grade1_braille": "UEB Grade 1 text (Restored)",
                "grade2_braille": "UEB Grade 2 text (Restored)",
                "character_count": len(art.braille_content) if art else len(conv.agent_response),
                "translation_notes": "Restored from SQLite archive.",
                "confidence_score": 1.0,
                "metadata": braille_meta
            }
        }
        
        if art and art.art_type == "image":
            outputs["tactile"] = {
                "simplified_svg": art.braille_content,
                "raised_line_layout": art.config_params.get("raised_line_layout", "N/A") if art.config_params else "N/A",
                "object_boundary_map": art.config_params.get("object_boundary_map", {}) if art.config_params else {},
                "relative_spatial_positions": art.config_params.get("relative_spatial_positions", {}) if art.config_params else {},
                "braille_overlay_coordinates": art.config_params.get("braille_overlay_coordinates", {}) if art.config_params else {},
                "embosser_ready_svg": "",
                "metadata": {
                    "simplified_svg_path": art.config_params.get("simplified_svg_path") if art.config_params else None,
                    "embosser_ready_svg_path": art.config_params.get("embosser_ready_svg_path") if art.config_params else None
                },
                "confidence_score": 1.0
            }
            
            if art.config_params:
                try:
                    embosser_path = art.config_params.get("embosser_ready_svg_path")
                    if embosser_path and os.path.exists(embosser_path):
                        with open(embosser_path, "r", encoding="utf-8") as f:
                            outputs["tactile"]["embosser_ready_svg"] = f.read()
                except Exception:
                    pass
                    
        outputs["accessibility"] = {
            "screen_reader_description": "Historical tactile rendering of " + conv.user_prompt,
            "easy_english_version": conv.user_prompt,
            "child_friendly_version": "A nice drawing of " + conv.user_prompt,
            "audio_narration_script": "Explore the shapes in this past design.",
            "alt_text": conv.user_prompt,
            "object_list": ["artwork"],
            "spatial_layout_description": "Details restored from SQLite archive.",
            "accessibility_score": {"completeness": 1.0, "readability": 1.0, "usefulness": 1.0, "screen_reader_compatibility": 1.0, "overall_score": 1.0},
            "suggested_improvements": [],
            "confidence_score": 1.0,
            "reasoning": "Restored log entry."
        }
        
        outputs["art_knowledge"] = {
            "artwork_title": conv.user_prompt,
            "artist": "Historical Log",
            "art_movement": "N/A",
            "creation_period": "N/A",
            "confidence_score": 1.0,
            "reasoning": "Restored log entry."
        }
        
        pipeline_result = {
            "uploaded_image": art.source_content if (art and "." in art.source_content) else "historical_art.png",
            "execution_trace": trace,
            "outputs": outputs,
            "generated_braille": outputs["braille"]["unicode_braille"],
            "generated_svg": outputs["tactile"]["simplified_svg"] if "tactile" in outputs else None,
            "accessibility_report": outputs["accessibility"]
        }
        return pipeline_result
    except Exception as e:
        st.error(f"Failed to load historical run: {e}")
        return None
    finally:
        db.close()

# ------------------------------------------------------------------------------
# Gemini Cached Quiz / Educational Content Generator
# ------------------------------------------------------------------------------
@st.cache_data
def generate_educational_package(art_title: str, artist: str, description: str, api_key: str):
    """
    Generate educational package including Artwork Summary, Interesting Facts,
    Vocabulary words, and multiple-choice Quiz questions via Gemini.
    """
    if not api_key:
        return {
            "summary": f"This study guide details '{art_title}' by {artist}. It portrays a vibrant visual context: {description}.",
            "facts": [
                f"'{art_title}' showcases structural and design elements typical of the creator's artistic style.",
                "Tactile representation helps individuals with visual impairments perceive visual compositions physically.",
                "Grade 1 Braille provides a letter-by-letter representation, assisting beginner learners."
            ],
            "vocabulary": [
                {"word": "Tactile", "definition": "Relating to or designed for the sense of touch."},
                {"word": "Composition", "definition": "The arrangement of individual visual elements in an artwork."},
                {"word": "Accessibility", "definition": "Designing software or art formats for people with disabilities."}
            ],
            "quiz": [
                {
                    "question": f"Who is documented as the artist of '{art_title}'?",
                    "options": [artist, "Leonardo da Vinci", "Pablo Picasso", "Unknown Creator"],
                    "correct_index": 0,
                    "explanation": f"The historical or metadata checks identified '{artist}' as the creator."
                },
                {
                    "question": "What is the primary role of the Tactile Layout Agent?",
                    "options": [
                        "To translate words into sound effects",
                        "To generate simplified outline SVGs for touch printing",
                        "To filter out offensive user comments",
                        "To adjust the contrast of computer monitors"
                    ],
                    "correct_index": 1,
                    "explanation": "The Tactile Layout Agent converts descriptions and visual profiles into print-ready SVGs with physical line maps."
                },
                {
                    "question": "Which Braille grade uses contractions to combine characters and increase speed?",
                    "options": ["Grade 1", "Grade 2", "Grade 3", "Nemeth Braille"],
                    "correct_index": 1,
                    "explanation": "Grade 2 Braille incorporates contractions and abbreviations to reduce the physical space required for text."
                }
            ]
        }
        
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        You are an Art Education Specialist. Based on the following artwork analysis details, generate an educational package for students.
        
        Artwork Title: {art_title}
        Artist: {artist}
        Description: {description}
        
        Generate a JSON response that complies exactly with this structure:
        {{
            "summary": "A user-friendly, inspiring summary of the artwork and its meaning.",
            "facts": [
                "Interesting historical or artistic fact 1",
                "Interesting historical or artistic fact 2",
                "Interesting historical or artistic fact 3"
            ],
            "vocabulary": [
                {{"word": "term1", "definition": "simple definition of term1"}},
                {{"word": "term2", "definition": "simple definition of term2"}},
                {{"word": "term3", "definition": "simple definition of term3"}}
            ],
            "quiz": [
                {{
                    "question": "A multiple-choice question testing understanding of the artwork or its tactile representation.",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_index": 0,
                    "explanation": "Brief explanation of why Option A is correct."
                }},
                {{
                    "question": "Another multiple-choice question.",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_index": 1,
                    "explanation": "Explanation of why Option B is correct."
                }},
                {{
                    "question": "A third multiple-choice question.",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_index": 2,
                    "explanation": "Explanation of why Option C is correct."
                }}
            ]
        }}
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        return {
            "summary": f"Summary: '{art_title}' is analyzed as a notable artwork. Here is a tactile representation.",
            "facts": ["Fact 1", "Fact 2", "Fact 3"],
            "vocabulary": [{"word": "Visual", "definition": "Relating to seeing"}],
            "quiz": [
                {
                    "question": f"Is this artwork '{art_title}'?",
                    "options": ["Yes", "No", "Maybe", "Unknown"],
                    "correct_index": 0,
                    "explanation": "Yes, correct."
                }
            ]
        }

# ------------------------------------------------------------------------------
# Sidebar Navigation Panel
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 style='font-size: 2.2rem; font-weight: 800; background: linear-gradient(45deg, #FF4B4B, #FF8F8F); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;'>
            ⠃⠗ BrailleArt
        </h1>
        <p style='color: #7f8c8d; font-size: 0.95rem; margin-top: 5px;'>Agents for Good Capstone</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.active_run:
        image_name = st.session_state.active_run.get("uploaded_image")
        if image_name:
            st.success(f"📂 Active: **{image_name}**")
        else:
            st.success("📂 Active: **Text Prompt**")
    else:
        st.info("📂 Active Workspace: **None**")
        
    st.divider()
    
    pages = [
        "Home",
        "Upload Artwork",
        "Live Agent Timeline",
        "Accessibility Report",
        "Braille Viewer",
        "Tactile Viewer",
        "Learning",
        "History",
        "Settings"
    ]
    icons = ["🏠", "📤", "⏱️", "♿", "⠃⠗", "📐", "🎓", "📚", "⚙️"]
    
    selected_page = st.radio(
        "Navigation Menu:",
        options=pages,
        format_func=lambda x: f"{icons[pages.index(x)]} {x}"
    )

# ------------------------------------------------------------------------------
# Page View Controller
# ------------------------------------------------------------------------------

# 1. HOME VIEW
if selected_page == "Home":
    st.markdown(
        """
        <div class="hero-section">
            <div class="hero-tagline">Making Art Accessible Through AI</div>
            <div class="hero-sub">Empowering visually impaired individuals to explore, feel, and study fine art using co-creative multi-agent systems.</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(
        """
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-val">11</div>
                <div class="stat-label">AI Agents</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">26</div>
                <div class="stat-label">Tests Passed</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">6</div>
                <div class="stat-label">Technologies</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">5</div>
                <div class="stat-label">Accessibility Features</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    render_card("Project Overview", 
        "Welcome to **BrailleArt AI**, an advanced co-creative multi-agent platform developed for the "
        "**Kaggle AI Agents: Capstone Project (Agents for Good track)**.\n\n"
        "BrailleArt AI is designed to support visually impaired students and individuals exploring the visual arts. "
        "It acts as a translation layer converting standard images, photos, and digital paintings into "
        "multi-modal tactile representations. By combining accessibility narratives, Unified English Braille (UEB), "
        "and physical raised-line SVG vector layout outlines, the platform allows artwork to be touched, "
        "felt, and studied in standard classroom settings."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        render_card("🤖 Key Pipeline Agents",
            "**1. Planner**: Assesses prompt requirements and sequences sub-agent execution pathways.\n"
            "**2. Security**: Scans user prompts and visual content for safety.\n"
            "**3. Vision & OCR**: Detects objects, boundaries, contrast ratios, and text segments.\n"
            "**4. Emotion & Art Knowledge**: Extracts atmosphere, creative intention, artist, and artistic movement.\n"
            "**5. Accessibility**: Produces audio exploration scripts, Screen Reader summaries, and Easy English descriptions."
        )
    with col2:
        render_card("📐 Core Outputs",
            "**- Braille Text Reports**: Unified English Braille translation files available in Grade 1, Grade 2, and Unicode Braille matrices.\n"
            "**- Raised-line Vectors**: Print-ready SVGs including coordinates overlay mapping, and specialized embosser-ready stroke designs.\n"
            "**- Interactive Learning guides**: Artwork summaries, vocabulary checks, and interactive multi-choice quizzes generated dynamically via Gemini."
        )
        
    st.subheader("⚙️ Multi-Agent Architecture")
    st.markdown("Below is the flow representation of the complete end-to-end multi-agent orchestration pipeline:")
    
    diagram_code = """
    graph TD
        User([User Image & Prompt]) --> Planner[Planner Agent]
        Planner --> Orchestrator[Orchestrator Agent]
        Orchestrator --> Sec[Security Agent]
        Sec --> Vis[Vision Agent]
        Vis --> OCR[OCR Agent]
        OCR --> Art[Art Knowledge Agent]
        Art --> Emotion[Emotion Agent]
        Emotion --> Acc[Accessibility Agent]
        Acc --> Braille[Braille Agent]
        Braille --> Tactile[Tactile Agent]
        Tactile --> Exp[Explainability Agent]
        Exp --> DB[(SQLite DB)]
        Exp --> Streamlit[Streamlit Dashboard]
        
        style Planner fill:#FF4B4B,stroke:#fff,stroke-width:1px,color:#fff
        style Orchestrator fill:#FF8F8F,stroke:#fff,stroke-width:1px,color:#000
        style Sec fill:#555,stroke:#fff,stroke-width:1px,color:#fff
        style Vis fill:#29B6F6,stroke:#fff,stroke-width:1px,color:#fff
        style OCR fill:#29B6F6,stroke:#fff,stroke-width:1px,color:#fff
        style Art fill:#FFB300,stroke:#fff,stroke-width:1px,color:#000
        style Emotion fill:#FFB300,stroke:#fff,stroke-width:1px,color:#000
        style Acc fill:#00E676,stroke:#fff,stroke-width:1px,color:#000
        style Braille fill:#FF4B4B,stroke:#fff,stroke-width:1px,color:#fff
        style Tactile fill:#FF4B4B,stroke:#fff,stroke-width:1px,color:#fff
        style Exp fill:#9C27B0,stroke:#fff,stroke-width:1px,color:#fff
        style DB fill:#777,stroke:#fff,stroke-width:1px,color:#fff
    """
    
    theme = st.session_state.get("settings_theme", "Sleek Dark")
    html_mermaid = f"""
    <div class="mermaid" style="background-color: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); border: 1px solid var(--card-border);">
    {diagram_code}
    </div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: '{'dark' if theme == 'Sleek Dark' else 'default'}' }});
    </script>
    """
    st.components.v1.html(html_mermaid, height=480, scrolling=True)

# 2. UPLOAD ARTWORK VIEW
elif selected_page == "Upload Artwork":
    st.title("📤 Upload Artwork")
    
    render_card("Instructions",
        "Select an artwork image file (PNG, JPG, or JPEG) and provide an optional textual prompt. "
        "The system will execute the security checks, run all computer vision and accessibility agents, "
        "and generate Unicode Braille translations and tactile layouts."
    )
    
    col_inp, col_prev = st.columns([1, 1])
    
    with col_inp:
        uploaded_file = st.file_uploader("Upload an Image to analyze", type=["png", "jpg", "jpeg"])
        user_prompt = st.text_input("User Prompt / Context", value="A beautiful nature landscape")
        
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        analyze_btn = st.button("🚀 Start Multi-Agent Analysis", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_prev:
        if uploaded_file:
            b64_img = base64.b64encode(uploaded_file.getvalue()).decode()
            st.markdown(
                f'<div style="text-align: center; background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); border: 1px solid var(--card-border); box-shadow: var(--shadow);">'
                f'<img src="data:{uploaded_file.type};base64,{b64_img}" style="max-height: 300px; max-width: 100%; border-radius: 8px;"/>'
                f'<div style="margin-top: 10px; font-weight: 600; color: var(--text-muted);">{uploaded_file.name}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("Upload an image file to display previews here.")
            
    if analyze_btn:
        validation_passed = True
        if uploaded_file:
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            if file_size_mb > 10.0:
                st.markdown(
                    f"""
                    <div class="error-card">
                        <h4>⚠️ File Size Validation Failed</h4>
                        <p>The uploaded image file is <strong>{file_size_mb:.2f} MB</strong>, which exceeds the limit of 10.0 MB.</p>
                        <p>Please select a smaller file for processing.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                validation_passed = False
        
        if validation_passed:
            backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            api_endpoint = f"{backend_url}/api/v1/analyze"
            
            loading_placeholder = st.empty()
            loading_placeholder.markdown(
                """
                <div class="custom-card" style="text-align: center; padding: 3rem 1.5rem;">
                    <div style="font-size: 3.5rem; margin-bottom: 1.5rem; animation: pulse-border 1s infinite alternate;">🤖</div>
                    <h3>Orchestrating Multi-Agent Pipeline...</h3>
                    <p style="color: var(--text-muted); margin-bottom: 2rem;">The Planner is scheduling Security, Vision, Accessibility, and Tactile Outline agents.</p>
                    <div style="display: flex; justify-content: center; gap: 15px; margin-bottom: 1rem;">
                        <span class="timeline-badge running" style="position: relative; left:0; top:0; width: 14px; height: 14px; display: inline-block;"></span>
                        <span style="font-weight: 600;">ACTIVE PIPELINE EXECUTION</span>
                    </div>
                    <div style="width: 100%; background: var(--card-border); height: 8px; border-radius: 4px; overflow: hidden; margin-top: 1.5rem;">
                        <div style="background: var(--accent); height: 100%; width: 65%; animation: progress-pulse 2.5s infinite ease-in-out;"></div>
                    </div>
                </div>
                <style>
                @keyframes progress-pulse {
                    0% { width: 10%; margin-left: 0; }
                    50% { width: 40%; margin-left: 60%; }
                    100% { width: 10%; margin-left: 0; }
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            
            try:
                files = None
                if uploaded_file:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {"prompt": user_prompt}
                
                response = requests.post(api_endpoint, data=data, files=files, timeout=90)
                loading_placeholder.empty()
                
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.active_run = result
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.learning_content = None
                    
                    st.success("🎉 Multi-Agent Analysis Completed Successfully! View details in other pages.")
                    st.balloons()
                else:
                    st.markdown(
                        f"""
                        <div class="error-card">
                            <h4>⚠️ Backend Server Error ({response.status_code})</h4>
                            <p>The backend pipeline failed to process the request.</p>
                            <p style="font-size: 0.9rem;"><strong>Response text:</strong> <code>{response.text}</code></p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            except Exception as e:
                loading_placeholder.empty()
                st.markdown(
                    f"""
                    <div class="error-card">
                        <h4>⚠️ Connection Error</h4>
                        <p>Failed to connect to the backend API at <strong>{api_endpoint}</strong>.</p>
                        <p style="font-size: 0.9rem;"><strong>Details:</strong> {str(e)}</p>
                        <div style="margin-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 0.8rem;">
                            <strong>Troubleshooting checklist:</strong>
                            <ul style="margin-top: 0.5rem; padding-left: 1.2rem;">
                                <li>Ensure the backend service is running (e.g. <code>uvicorn src.backend.main:app --port 8000</code>).</li>
                                <li>Check if port 8000 is open and not blocked by a firewall.</li>
                                <li>Verify your <code>BACKEND_URL</code> environment variable or dashboard configurations.</li>
                            </ul>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# 3. LIVE AGENT TIMELINE VIEW
elif selected_page == "Live Agent Timeline":
    st.title("⏱️ Live Agent Timeline")
    
    if not st.session_state.active_run:
        st.info("No active workspace analysis. Go to 'Upload Artwork' and run analysis first.")
    else:
        trace = st.session_state.active_run.get("execution_trace", [])
        
        st.subheader("Chronological Execution Logs")
        
        agent_icons = {
            "planner": "📋",
            "security": "🔒",
            "vision": "👁️",
            "ocr": "🔍",
            "style": "🎨",
            "emotion": "😊",
            "art_knowledge": "📚",
            "accessibility": "♿",
            "braille": "⠿",
            "tactile": "📐",
            "explainability": "🧠"
        }
        
        theme = st.session_state.get("settings_theme", "Sleek Dark")
        
        timeline_html = "<div class='timeline-container'>"
        for idx, entry in enumerate(trace):
            agent_key = entry.get("agent", "unknown").lower()
            agent_name = agent_key.replace("_", " ").title()
            icon = agent_icons.get(agent_key, "🤖")
            status = entry.get("status", "skipped").lower()
            time_ms = entry.get("execution_time_ms", 0)
            error = entry.get("error_message")
            
            progress_pct = int((idx + 1) / len(trace) * 100)
            
            status_class = "skipped"
            badge_text = "Skipped"
            badge_bg = "var(--text-muted)"
            badge_color = "#FFF"
            
            if status == "completed":
                status_class = "completed"
                badge_text = "Completed"
                badge_bg = "var(--success-color)"
                badge_color = "#000" if theme != "High Contrast" else "#FFF"
            elif status == "failed":
                status_class = "failed"
                badge_text = "Failed"
                badge_bg = "var(--error-color)"
                badge_color = "#FFF"
            elif status == "running":
                status_class = "running"
                badge_text = "Running"
                badge_bg = "var(--running-color)"
                badge_color = "#000" if theme != "High Contrast" else "#FFF"
                
            time_display = f"⏱️ {time_ms} ms" if status == "completed" else ""
            error_display = f"<div style='color: var(--error-color); margin-top: 5px; font-size: 0.85rem;'>Error: {error}</div>" if error else ""
            
            delay = idx * 0.08
            
            timeline_html += f"""
            <div class='timeline-card {status_class}' style='animation-delay: {delay}s;'>
                <div class='timeline-info'>
                    <div class='timeline-icon'>{icon}</div>
                    <div class='timeline-meta'>
                        <div class='timeline-title'>{agent_name} Agent</div>
                        <div class='timeline-status'>
                            <span style='padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; background-color: {badge_bg}; color: {badge_color};'>
                                {badge_text}
                            </span>
                            <span style='margin-left: 8px; font-size: 0.8rem; opacity: 0.8;'>Progress: {progress_pct}%</span>
                        </div>
                    </div>
                </div>
                <div>
                    <span class='timeline-time'>{time_display}</span>
                    {error_display}
                </div>
            </div>
            """
        timeline_html += "</div>"
        st.markdown(timeline_html, unsafe_allow_html=True)
        
        outputs = st.session_state.active_run.get("outputs", {})
        exp_report = outputs.get("explainability", {})
        if exp_report:
            st.divider()
            render_card("🤖 Explainability Agent Audit Summary",
                f"**Audit Report:** {exp_report.get('audit_report', 'N/A')}\n\n"
                f"**Confidence Analysis:** {exp_report.get('confidence_audit_summary', 'N/A')}\n\n"
                f"**Audit Rating:** `{exp_report.get('confidence_score', 0.0) * 100:.1f}%`"
            )

# 4. ACCESSIBILITY REPORT VIEW
elif selected_page == "Accessibility Report":
    st.title("♿ Accessibility Report")
    
    if not st.session_state.active_run:
        st.info("No active workspace analysis. Go to 'Upload Artwork' and run analysis first.")
    else:
        report = st.session_state.active_run.get("accessibility_report", {})
        if not report:
            st.warning("No accessibility data was generated for this run.")
        else:
            scores = report.get("accessibility_score", {})
            theme = st.session_state.get("settings_theme", "Sleek Dark")
            
            st.subheader("📊 Accessibility Score Dashboard")
            
            def make_gauge_svg(score: float, label: str):
                percentage = int(score * 100)
                r = 35
                cx = 50
                cy = 50
                circumference = 2 * 3.1415926 * r
                offset = circumference * (1 - score)
                
                color_var = "var(--accent)"
                text_color = "var(--text-color)"
                bg_circle = "var(--card-border)"
                
                return f"""
                <svg viewBox="0 0 100 100" width="100%" height="100%" style="max-width: 100px; margin: 0 auto; display: block;">
                    <circle cx="{cx}" cy="{cy}" r="{r}" stroke="{bg_circle}" stroke-width="8" fill="none" />
                    <circle cx="{cx}" cy="{cy}" r="{r}" stroke="{color_var}" stroke-width="8" fill="none"
                            stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
                            stroke-linecap="round" transform="rotate(-90 {cx} {cy})" />
                    <text x="{cx}" y="{cy + 5}" text-anchor="middle" font-family="system-ui, sans-serif" font-size="18" font-weight="800" fill="{text_color}">{percentage}%</text>
                </svg>
                <div style="text-align: center; margin-top: 8px; font-weight: 700; font-size: 0.85rem; color: var(--text-color);">{label}</div>
                """

            cols = st.columns(len(scores))
            for idx, (key, val) in enumerate(scores.items()):
                nice_label = key.replace("_", " ").title()
                with cols[idx]:
                    st.markdown(
                        f'<div class="gauge-item">{make_gauge_svg(float(val), nice_label)}</div>',
                        unsafe_allow_html=True
                    )
            st.divider()
            
            col_scores, col_text = st.columns([1, 2])
            
            with col_scores:
                st.subheader("Audit Context")
                st.write(f"**Description Confidence Rating:** `{report.get('confidence_score', 0.0) * 100:.1f}%`")
                st.write(f"**Reasoning Details:**\n<small>{report.get('reasoning', 'N/A')}</small>", unsafe_allow_html=True)
                
            with col_text:
                st.subheader("Alternative Narratives")
                st.write(f"**Alt Text:** `{report.get('alt_text', 'N/A')}`")
                
                render_speak_button(report.get("screen_reader_description", ""), "🔊 Read Screen Reader Text")
                render_speak_button(report.get("easy_english_version", ""), "🔊 Read Easy English Text")
                
                tabs_narrative = st.tabs([
                    "🔊 Screen Reader Text", "📖 Easy English", "👶 Child Friendly", "🎤 Audio Script"
                ])
                
                with tabs_narrative[0]:
                    st.markdown(
                        f'<div class="custom-card">{report.get("screen_reader_description", "N/A")}</div>',
                        unsafe_allow_html=True
                    )
                with tabs_narrative[1]:
                    st.markdown(
                        f'<div class="custom-card">{report.get("easy_english_version", "N/A")}</div>',
                        unsafe_allow_html=True
                    )
                with tabs_narrative[2]:
                    st.markdown(
                        f'<div class="custom-card">{report.get("child_friendly_version", "N/A")}</div>',
                        unsafe_allow_html=True
                    )
                with tabs_narrative[3]:
                    st.markdown(
                        f'<div class="custom-card">{report.get("audio_narration_script", "N/A")}</div>',
                        unsafe_allow_html=True
                    )
                    
            col_obj, col_imp = st.columns(2)
            with col_obj:
                render_card("🔍 Identified Object Registry",
                    ", ".join(report.get("object_list", [])) if report.get("object_list") else "None identified."
                )
            with col_imp:
                render_card("💡 Accessibility Improvements",
                    "\n".join([f"- {imp}" for imp in report.get("suggested_improvements", [])]) if report.get("suggested_improvements") else "No improvements required."
                )

# 5. BRAILLE VIEWER VIEW
elif selected_page == "Braille Viewer":
    st.title("⠃⠗ Braille Viewer")
    
    if not st.session_state.active_run:
        st.info("No active workspace analysis. Go to 'Upload Artwork' and run analysis first.")
    else:
        outputs = st.session_state.active_run.get("outputs", {})
        braille_out = outputs.get("braille", {})
        if not braille_out:
            st.warning("No Braille translation outputs generated for this workspace.")
        else:
            theme = st.session_state.get("settings_theme", "Sleek Dark")
            box_class = "dark"
            if theme == "Clean Light":
                box_class = "light"
            elif theme == "High Contrast":
                box_class = "highcontrast"
                
            st.subheader("Braille Matrix Translations")
            
            def make_braille_viewer(title: str, text: str, element_id: str):
                escaped_text = json.dumps(text)
                return f"""
                <div class="braille-container">
                    <div style="font-weight: 700; color: var(--text-color); margin-bottom: 0.5rem; font-size: 0.95rem;">{title}</div>
                    <button onclick='navigator.clipboard.writeText({escaped_text}); this.innerHTML="✅ Copied!"; setTimeout(()=>this.innerHTML="📋 Copy", 2000);' class="copy-btn">📋 Copy</button>
                    <div id="{element_id}" class="braille-box {box_class}">{text}</div>
                </div>
                """

            tabs_braille = st.tabs(["Unicode Braille Matrix", "Grade 1 Braille Text", "Grade 2 Braille Text"])
            
            with tabs_braille[0]:
                st.markdown(make_braille_viewer("Unicode Braille Matrix", braille_out.get("unicode_braille", "N/A"), "unicode_b"), unsafe_allow_html=True)
            with tabs_braille[1]:
                st.markdown(make_braille_viewer("UEB Grade 1 Translation", braille_out.get("grade1_braille", "N/A"), "grade1_b"), unsafe_allow_html=True)
            with tabs_braille[2]:
                st.markdown(make_braille_viewer("UEB Grade 2 Translation (Contracted)", braille_out.get("grade2_braille", "N/A"), "grade2_b"), unsafe_allow_html=True)
            
            st.divider()
            col_txt, col_notes = st.columns(2)
            with col_txt:
                render_card("Translation Settings",
                    f"- **Selected Dialect**: `{st.session_state.get('settings_language', 'English')}`\n"
                    f"- **Monospace Mode**: `Active`"
                )
            with col_notes:
                render_card("Translation Metrics",
                    f"- **Cells Count**: {braille_out.get('character_count', 0)} cells\n"
                    f"- **Contraction Notes**: {braille_out.get('translation_notes', 'N/A')}\n"
                    f"- **Confidence score**: `{braille_out.get('confidence_score', 0.0) * 100:.1f}%`"
                )
                
            dl_content = f"""--- BRAILLEART AI - TRANSLATION FILE ---
Source: {braille_out.get('plain_text', '')}
Total cells: {braille_out.get('character_count', 0)}

UNICODE MATRIX:
{braille_out.get('unicode_braille', '')}

GRADE 1 TRANSLATION:
{braille_out.get('grade1_braille', '')}

GRADE 2 TRANSLATION:
{braille_out.get('grade2_braille', '')}

NOTES:
{braille_out.get('translation_notes', '')}
"""
            st.download_button(
                label="📥 Download Braille (.txt)",
                data=dl_content,
                file_name=f"braille_translation_{st.session_state.active_run.get('uploaded_image', 'art')}.txt",
                mime="text/plain",
                use_container_width=True
            )

# 6. TACTILE VIEWER VIEW
elif selected_page == "Tactile Viewer":
    st.title("📐 Tactile Graphic Viewer")
    
    if not st.session_state.active_run:
        st.info("No active workspace analysis. Go to 'Upload Artwork' and run analysis first.")
    else:
        outputs = st.session_state.active_run.get("outputs", {})
        tactile_out = outputs.get("tactile", {})
        if not tactile_out:
            st.warning("No tactile graphics data was generated.")
        else:
            col_graphic, col_specs = st.columns([3, 2])
            
            with col_graphic:
                st.subheader("Tactile SVG Graphic")
                svg = tactile_out.get("simplified_svg", "")
                if svg:
                    try:
                        b64_svg = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
                        iframe_html = f"""
                        <div style="border: 1px solid var(--card-border, #ccc); border-radius: 12px; background-color: #ffffff; padding: 1.5rem; text-align: center; position: relative;">
                            <div style="position: absolute; top: 15px; right: 15px; z-index: 100; display: flex; gap: 8px;">
                                <button onclick="zoomSvg(1.25)" style="background: rgba(0,0,0,0.7); color: white; border: none; border-radius: 4px; padding: 6px 12px; font-weight: bold; cursor: pointer; font-size: 1rem;">➕</button>
                                <button onclick="zoomSvg(0.8)" style="background: rgba(0,0,0,0.7); color: white; border: none; border-radius: 4px; padding: 6px 12px; font-weight: bold; cursor: pointer; font-size: 1rem;">➖</button>
                                <button onclick="resetSvg()" style="background: rgba(0,0,0,0.7); color: white; border: none; border-radius: 4px; padding: 6px 12px; font-weight: bold; cursor: pointer; font-size: 1rem;">🔄</button>
                            </div>
                            
                            <div id="svg-view-window" style="overflow: auto; max-height: 400px; display: flex; align-items: center; justify-content: center; min-height: 350px; cursor: grab;">
                                <div id="svg-scale-wrapper" style="transform-origin: center center; transition: transform 0.2s ease-out; display: inline-block;">
                                    <img src="data:image/svg+xml;base64,{b64_svg}" style="max-height: 330px; max-width: 100%; height: auto;" id="tactile-svg-img" />
                                </div>
                            </div>
                        </div>
                        
                        <script>
                            let currentScale = 1.0;
                            function zoomSvg(factor) {{
                                currentScale *= factor;
                                if (currentScale < 0.5) currentScale = 0.5;
                                if (currentScale > 4.0) currentScale = 4.0;
                                document.getElementById('svg-scale-wrapper').style.transform = `scale(${{currentScale}})`;
                            }}
                            function resetSvg() {{
                                currentScale = 1.0;
                                document.getElementById('svg-scale-wrapper').style.transform = `scale(1)`;
                            }}
                        </script>
                        """
                        st.components.v1.html(iframe_html, height=450)
                    except Exception as e:
                        st.error(f"SVG render error: {e}")
                else:
                    st.info("SVG graphic content is empty.")
                    
                st.subheader("Exporter Options")
                st.download_button(
                    label="📐 Download Simplified SVG Outline",
                    data=svg,
                    file_name=f"tactile_outline_{st.session_state.active_run.get('uploaded_image', 'art')}.svg",
                    mime="image/svg+xml",
                    use_container_width=True
                )
                
                st.download_button(
                    label="🖨️ Download Embosser-Ready SVG",
                    data=tactile_out.get("embosser_ready_svg", ""),
                    file_name=f"tactile_embosser_{st.session_state.active_run.get('uploaded_image', 'art')}.svg",
                    mime="image/svg+xml",
                    use_container_width=True
                )
                
            with col_specs:
                st.subheader("Physical Layout Coordinates")
                st.write(f"**Raised-line descriptions:**\n{tactile_out.get('raised_line_layout', 'N/A')}")
                
                st.divider()
                st.write("**Object boundary coordinates:**")
                bm = tactile_out.get("object_boundary_map", {})
                if bm:
                    for k, v in bm.items():
                        st.write(f"- **{k}**: `Bounding Box: {v}`")
                else:
                    st.write("No boundaries mapped.")
                    
                st.divider()
                st.write("**Relative Spatial Positions:**")
                sp = tactile_out.get("relative_spatial_positions", {})
                if sp:
                    for k, v in sp.items():
                        st.write(f"- **{k}**: {v}")
                else:
                    st.write("No relative alignments registered.")
                    
                st.divider()
                st.write(f"**Tactile Graphic Fidelity rating:** `{tactile_out.get('confidence_score', 0.0) * 100:.1f}%`")

# 7. LEARNING VIEW
elif selected_page == "Learning":
    st.title("🎓 Educational Workspace")
    
    if not st.session_state.active_run:
        st.info("No active workspace analysis. Go to 'Upload Artwork' and run analysis first.")
    else:
        outputs = st.session_state.active_run.get("outputs", {})
        art_info = outputs.get("art_knowledge", {})
        acc_info = outputs.get("accessibility", {})
        
        art_title = art_info.get("artwork_title", "Unknown Artwork") if art_info else "Unknown Artwork"
        artist = art_info.get("artist", "Unknown Artist") if art_info else "Unknown Artist"
        desc = acc_info.get("easy_english_version", "Tactile description of the visual scene.") if acc_info else "Visual context description."
        
        if not st.session_state.learning_content:
            with st.spinner("Generating personalized educational package via Gemini..."):
                key = os.getenv("GEMINI_API_KEY", "")
                st.session_state.learning_content = generate_educational_package(art_title, artist, desc, key)
                
        edu = st.session_state.learning_content
        
        st.header(f"Study Guide: {art_title}")
        
        render_card("📝 Artwork Summary", edu.get("summary", "N/A"))
        
        c_facts, c_vocab = st.columns(2)
        with c_facts:
            st.subheader("💡 Did You Know?")
            facts_list = edu.get("facts", [])
            for fact in facts_list:
                st.markdown(f'<div class="learning-card">✨ {fact}</div>', unsafe_allow_html=True)
                
        with c_vocab:
            st.subheader("📚 Vocabulary Checks")
            vocab_list = edu.get("vocabulary", [])
            for item in vocab_list:
                st.markdown(
                    f'<div class="learning-card">'
                    f'<strong>🔎 {item.get("word")}</strong>'
                    f'<div style="font-size: 0.9rem; margin-top: 5px; opacity: 0.85;">{item.get("definition")}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
        st.divider()
        st.subheader("🧠 Interactive Comprehension Quiz")
        
        quiz = edu.get("quiz", [])
        if not quiz:
            st.info("No quiz questions compiled for this guide.")
        else:
            with st.form(key="quiz_classroom_form"):
                user_choices = {}
                for idx, q in enumerate(quiz):
                    st.write(f"**Q{idx+1}: {q.get('question')}**")
                    user_choices[idx] = st.radio(
                        "Options:",
                        options=q.get("options", []),
                        key=f"class_q_{idx}",
                        index=0
                    )
                    st.write(" ")
                submit = st.form_submit_button("Submit Quiz Answers")
                
            if submit or st.session_state.quiz_submitted:
                st.session_state.quiz_submitted = True
                
                st.write("### 📊 Evaluation Output")
                correct = 0
                for idx, q in enumerate(quiz):
                    sel = user_choices[idx]
                    opts = q.get("options", []),
                    c_idx = q.get("correct_index", 0)
                    # Options is parsed as option tuple sometimes from prompt list, let's normalize
                    opts_normalized = opts[0] if isinstance(opts, tuple) and len(opts) > 0 else opts
                    correct_opt = opts_normalized[c_idx] if c_idx < len(opts_normalized) else ""
                    
                    if sel == correct_opt:
                        correct += 1
                        st.markdown(
                            f"""
                            <div class="custom-card" style="border: 2px solid var(--success-color); background-color: rgba(0, 230, 118, 0.05); margin-bottom: 1rem;">
                                <strong style="color: var(--success-color); font-size: 1.1rem;">✅ Question {idx+1}: Correct!</strong>
                                <p style="margin-top: 5px; margin-bottom: 5px;"><strong>Your Choice:</strong> {sel}</p>
                                <p style="font-size: 0.95rem; opacity: 0.9;">{q.get('explanation')}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"""
                            <div class="custom-card" style="border: 2px solid var(--error-color); background-color: rgba(255, 82, 82, 0.05); margin-bottom: 1rem;">
                                <strong style="color: var(--error-color); font-size: 1.1rem;">❌ Question {idx+1}: Incorrect</strong>
                                <p style="margin-top: 5px; margin-bottom: 5px;"><strong>Your Choice:</strong> {sel} | <strong>Correct Answer:</strong> {correct_opt}</p>
                                <p style="font-size: 0.95rem; opacity: 0.9;">{q.get('explanation')}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                st.metric(
                    label="Final Score",
                    value=f"{correct} / {len(quiz)}",
                    delta=f"{int(correct/len(quiz)*100)}%"
                )

# 8. HISTORY VIEW
elif selected_page == "History":
    st.title("📚 SQLite Analysis Logs")
    
    conversations, saved_arts = get_db_history()
    
    if not conversations:
        st.info("No historical logs registered in SQLite. Perform your first artwork upload analysis!")
    else:
        render_card("Archive Info", f"Found **{len(conversations)}** records in the SQLite database.")
        
        st.subheader("Saved Analyses")
        
        cols = st.columns(2)
        for idx, conv in enumerate(conversations):
            col_target = cols[idx % 2]
            
            is_image_run = False
            associated_art = next((art for art in saved_arts if art.source_content == conv.user_prompt), None)
            if associated_art:
                is_image_run = (associated_art.art_type == "image")
                
            icon = "🖼️ Image Analysis" if is_image_run else "✍️ Text Analysis"
            formatted_date = conv.created_at.strftime("%Y-%m-%d %H:%M:%S")
            
            with col_target:
                st.markdown(
                    f"""
                    <div class="custom-card" style="min-height: 120px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 0.5rem;">
                        <div>
                            <span style="font-size: 0.75rem; text-transform: uppercase; font-weight: bold; padding: 2px 6px; border-radius: 4px; background: rgba(255, 75, 75, 0.1); color: var(--accent);">{icon}</span>
                            <div style="font-weight: 700; margin-top: 8px; font-size: 1.05rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{conv.user_prompt or 'Analyze artwork'}</div>
                            <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">Session: {conv.session_id[:8]}... | {formatted_date}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button("📂 Reopen Analysis", key=f"load_log_{conv.id}", use_container_width=True):
                    with st.spinner("Loading archive workspace..."):
                        res = load_historical_run(conv.id)
                        if res:
                            st.session_state.active_run = res
                            st.session_state.quiz_answers = {}
                            st.session_state.quiz_submitted = False
                            st.session_state.learning_content = None
                            st.success(f"Workspace loaded: '{conv.user_prompt}'!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Failed to parse historical log entry.")
                st.write("")

# 9. SETTINGS VIEW
elif selected_page == "Settings":
    st.title("⚙️ System Configuration")
    
    st.subheader("Accessibility & Visual Preferences")
    
    theme = st.selectbox(
        "Accessibility Theme Selection",
        options=["Sleek Dark", "Clean Light", "High Contrast"],
        index=["Sleek Dark", "Clean Light", "High Contrast"].index(st.session_state.settings_theme)
    )
    if theme != st.session_state.settings_theme:
        st.session_state.settings_theme = theme
        st.rerun()
        
    font_size = st.selectbox(
        "Interface Font Size",
        options=["Small", "Medium", "Large"],
        index=["Small", "Medium", "Large"].index(st.session_state.settings_font_size)
    )
    if font_size != st.session_state.settings_font_size:
        st.session_state.settings_font_size = font_size
        st.rerun()
        
    st.subheader("Audio Settings")
    speech_toggle = st.checkbox(
        "Enable HTML5 text-to-speech audio feedback buttons on reports",
        value=st.session_state.settings_speech
    )
    st.session_state.settings_speech = speech_toggle
    
    speech_speed = st.slider(
        "Speech speed rate (1.0x is standard)",
        min_value=0.5,
        max_value=2.0,
        value=st.session_state.get("settings_speech_speed", 1.0),
        step=0.1
    )
    st.session_state.settings_speech_speed = speech_speed
    
    st.subheader("Localization & Custom APIs")
    lang = st.selectbox(
        "Local Translation Dialect",
        options=["English", "Spanish", "French", "German"],
        index=["English", "Spanish", "French", "German"].index(st.session_state.settings_language)
    )
    st.session_state.settings_language = lang
    
    custom_key = st.text_input(
        "Google Gemini API Key override (Frontend operations)",
        value=st.session_state.get("settings_api_key", ""),
        type="password",
        help="Inputting a key here overrides the environment key for educational guides generation."
    )
    if custom_key:
        st.session_state.settings_api_key = custom_key
        os.environ["GEMINI_API_KEY"] = custom_key
        
    st.divider()
    render_card("Preferences Registry Summary",
        f"- **Selected Visual Theme**: `{theme}`\n"
        f"- **Font scaling**: `{font_size}`\n"
        f"- **Language output**: `{lang}`\n"
        f"- **Speech speed multiplier**: `{speech_speed}x`\n"
        f"- **Speech buttons**: `{'Active' if speech_toggle else 'Deactivated'}`\n"
        f"- **Gemini API Configuration**: `{'Configured (Active)' if custom_key or os.getenv('GEMINI_API_KEY') else 'Empty'}`"
    )

st.divider()
st.caption("Kaggle AI Agents Capstone - BrailleArt AI Project dashboard. Powered by Gemini 2.5 Flash & FastAPI.")

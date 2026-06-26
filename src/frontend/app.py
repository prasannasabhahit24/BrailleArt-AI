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
    if font_size == "Small":
        font_size_px = "14px"
    elif font_size == "Large":
        font_size_px = "20px"
        
    card_class = "card"
    if theme == "Clean Light":
        card_class = "card-light"
    elif theme == "High Contrast":
        card_class = "card-highcontrast"

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;600;700&display=swap');
        
        .stApp {{
            font-family: 'Inter', sans-serif;
            font-size: {font_size_px};
        }}
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Outfit', sans-serif;
        }}
        
        /* Premium Card Component */
        .custom-card {{
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
        }}
        .custom-card h4 {{
            margin-top: 0;
            margin-bottom: 0.8rem;
            font-weight: 700;
        }}
        
        /* Sleek Dark Theme Styles */
        .card {{
            background: rgba(28, 28, 30, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            color: #F2F2F7;
        }}
        
        /* Clean Light Theme Styles */
        .card-light {{
            background: rgba(255, 255, 255, 0.85);
            border: 1px solid rgba(0, 0, 0, 0.1);
            box-shadow: 0 8px 24px 0 rgba(0, 0, 0, 0.08);
            color: #1C1C1E;
        }}
        
        /* High Contrast Theme Styles */
        .card-highcontrast {{
            background: #000000;
            border: 3px solid #FFFF00;
            border-radius: 8px;
            color: #FFFFFF;
        }}
        
        /* Chronological Timeline */
        .timeline-container {{
            margin: 1.5rem 0;
        }}
        .timeline-step {{
            border-left: 2px solid rgba(255, 75, 75, 0.3);
            padding-left: 1.5rem;
            position: relative;
            padding-bottom: 1.5rem;
        }}
        .timeline-step.completed {{
            border-left: 2px solid #00E676;
        }}
        .timeline-step.failed {{
            border-left: 2px solid #D32F2F;
        }}
        .timeline-step.running {{
            border-left: 2px dashed #29B6F6;
        }}
        .timeline-step.skipped {{
            border-left: 2px solid #555555;
            opacity: 0.6;
        }}
        
        .timeline-badge {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            position: absolute;
            left: -7px;
            top: 6px;
            background-color: #7f8c8d;
        }}
        .timeline-badge.completed {{
            background-color: #00E676;
            box-shadow: 0 0 8px #00E676;
        }}
        .timeline-badge.failed {{
            background-color: #D32F2F;
            box-shadow: 0 0 8px #D32F2F;
        }}
        .timeline-badge.running {{
            background-color: #29B6F6;
            box-shadow: 0 0 8px #29B6F6;
        }}
        .timeline-badge.skipped {{
            background-color: #555555;
        }}
        
        /* Monospace braille outputs */
        .braille-box {{
            font-family: 'Courier New', Courier, monospace;
            font-size: 22px;
            line-height: 1.3;
            letter-spacing: 2px;
            padding: 1.5rem;
            border-radius: 12px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-all;
            margin-bottom: 1.5rem;
        }}
        .braille-box.dark {{
            background-color: #0a0b0e;
            color: #00FF66;
            border: 1px solid #1f242d;
            box-shadow: 0 0 15px rgba(0, 255, 102, 0.2);
        }}
        .braille-box.light {{
            background-color: #f4f4f6;
            color: #1c1c1e;
            border: 1px solid #e5e5ea;
        }}
        .braille-box.highcontrast {{
            background-color: #000000;
            color: #FFFF00;
            border: 3px solid #FFFF00;
            font-size: 26px;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_custom_css()

# Helper to render cards
def render_card(title: str, content: str = "", html_content: str = ""):
    theme = st.session_state.get("settings_theme", "Sleek Dark")
    card_class = "card"
    if theme == "Clean Light":
        card_class = "card-light"
    elif theme == "High Contrast":
        card_class = "card-highcontrast"
        
    title_html = f"<h4>{title}</h4>" if title else ""
    body_html = f"<p style='white-space: pre-line;'>{content}</p>" if content else ""
    full_html = f"<div class='custom-card {card_class}'>{title_html}{body_html}{html_content}</div>"
    st.markdown(full_html, unsafe_allow_html=True)

# Helper to render speech synthesis buttons
def render_speak_button(text_to_speak: str, label: str = "🔊 Read Aloud"):
    if not text_to_speak or not st.session_state.get("settings_speech", False):
        return
    # Sanitize text
    escaped_text = json.dumps(text_to_speak)
    btn_id = f"speak_btn_{abs(hash(text_to_speak))}"
    html_speak = f"""
    <button id="{btn_id}" style="
        background-color: #FF4B4B;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: bold;
        margin-bottom: 10px;
    ">
        {label}
    </button>
    <script>
        document.getElementById("{btn_id}").addEventListener("click", () => {{
            const utterance = new SpeechSynthesisUtterance({escaped_text});
            utterance.rate = 1.0;
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
    st.title("🏠 Home - BrailleArt AI Project")
    
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
    
    # Render Mermaid Architecture diagram
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
    """
    
    html_mermaid = f"""
    <div class="mermaid" style="background-color: #1e1e1e; padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
    {diagram_code}
    </div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
    </script>
    """
    st.components.v1.html(html_mermaid, height=450, scrolling=True)

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
        
        analyze_btn = st.button("🚀 Start Multi-Agent Analysis", use_container_width=True)
        
    with col_prev:
        if uploaded_file:
            st.image(uploaded_file, caption="Selected Artwork Preview", use_container_width=True)
        else:
            st.info("Upload an image file to display previews here.")
            
    if analyze_btn:
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        api_endpoint = f"{backend_url}/api/v1/analyze"
        
        # Display Progress Animation
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        steps = [
            ("Initializing agent pipeline...", 10),
            ("Securing workspace & verifying safety...", 25),
            ("Running computer vision shape outlines...", 45),
            ("Extracting text and symbols via OCR...", 60),
            ("Synthesizing art history details & emotions...", 75),
            ("Compiling Screen-Reader profiles...", 85),
            ("Translating characters to Braille UEB...", 95),
            ("Finalizing SVGs & compiling logs...", 100)
        ]
        
        with st.spinner("Processing request on the backend..."):
            try:
                # Prepare payload
                files = None
                if uploaded_file:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {"prompt": user_prompt}
                
                # Mock progress steps before trigger
                for idx, (label, val) in enumerate(steps[:5]):
                    status_text.text(f"Step {idx+1}: {label}")
                    progress_bar.progress(val)
                    time.sleep(0.3)
                
                response = requests.post(api_endpoint, data=data, files=files, timeout=90)
                
                if response.status_code == 200:
                    # Final progress
                    for idx, (label, val) in enumerate(steps[5:]):
                        status_text.text(f"Step {idx+6}: {label}")
                        progress_bar.progress(val)
                        time.sleep(0.2)
                        
                    result = response.json()
                    st.session_state.active_run = result
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.learning_content = None
                    
                    st.success("🎉 Multi-Agent Analysis Completed Successfully! View details in other pages.")
                    st.balloons()
                else:
                    st.error(f"Backend returned error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend at {api_endpoint}. Check if server is running: {e}")

# 3. LIVE AGENT TIMELINE VIEW
elif selected_page == "Live Agent Timeline":
    st.title("⏱️ Live Agent Timeline")
    
    if not st.session_state.active_run:
        st.info("No active workspace analysis. Go to 'Upload Artwork' and run analysis first.")
    else:
        trace = st.session_state.active_run.get("execution_trace", [])
        
        st.subheader("Chronological Execution Logs")
        
        timeline_html = "<div class='timeline-container'>"
        for entry in trace:
            agent = entry.get("agent", "unknown").upper()
            status = entry.get("status", "skipped").lower()
            time_ms = entry.get("execution_time_ms", 0)
            error = entry.get("error_message")
            
            status_class = "skipped"
            badge_text = "Skipped"
            if status == "completed":
                status_class = "completed"
                badge_text = "Completed"
            elif status == "failed":
                status_class = "failed"
                badge_text = "Failed"
            elif status == "running":
                status_class = "running"
                badge_text = "Running"
                
            time_display = f"⏱️ {time_ms} ms" if status == "completed" else ""
            error_display = f"<br/><small style='color: #ff5252;'>Error: {error}</small>" if error else ""
            
            timeline_html += f"""
            <div class='timeline-step {status_class}'>
                <div class='timeline-badge {status_class}'></div>
                <strong style='font-size: 1.1em;'>{agent} Agent</strong>
                <span style='margin-left: 10px; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; 
                             background-color: {"#00E676" if status_class=="completed" else "#D32F2F" if status_class=="failed" else "#29B6F6" if status_class=="running" else "#555"};
                             color: {"#000" if status_class=="completed" else "#FFF"};'>
                    {badge_text}
                </span>
                <span style='float: right; color: #888;'>{time_display}</span>
                {error_display}
            </div>
            """
        timeline_html += "</div>"
        
        st.markdown(timeline_html, unsafe_allow_html=True)
        
        # Display Explainability audit summary
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
            
            col_scores, col_text = st.columns([1, 2])
            
            with col_scores:
                st.subheader("Accessibility Metrics")
                for key, val in scores.items():
                    nice_key = key.replace("_", " ").title()
                    st.write(f"**{nice_key}** ({int(val * 100)}%)")
                    st.progress(float(val))
                    
                st.divider()
                st.write(f"**Description Confidence Rating:** `{report.get('confidence_score', 0.0) * 100:.1f}%`")
                st.write(f"**Reasoning Details:**\n<small>{report.get('reasoning', 'N/A')}</small>", unsafe_allow_html=True)
                
            with col_text:
                st.subheader("Alternative Narratives")
                st.write(f"**Alt Text:** `{report.get('alt_text', 'N/A')}`")
                
                # Speech synthesis support
                render_speak_button(report.get("screen_reader_description", ""), "🔊 Read Screen Reader Text")
                render_speak_button(report.get("easy_english_version", ""), "🔊 Read Easy English Text")
                
                tabs_narrative = st.tabs([
                    "🔊 Screen Reader Text", "📖 Easy English", "👶 Child Friendly", "🎤 Audio Script"
                ])
                
                with tabs_narrative[0]:
                    st.write(report.get("screen_reader_description", "N/A"))
                with tabs_narrative[1]:
                    st.write(report.get("easy_english_version", "N/A"))
                with tabs_narrative[2]:
                    st.write(report.get("child_friendly_version", "N/A"))
                with tabs_narrative[3]:
                    st.write(report.get("audio_narration_script", "N/A"))
                    
            # Bottom detail summary
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
                
            st.subheader("Unicode Braille Matrix")
            st.markdown(f'<div class="braille-box {box_class}">{braille_out.get("unicode_braille", "N/A")}</div>', unsafe_allow_html=True)
            
            col_txt, col_notes = st.columns(2)
            with col_txt:
                render_card("Grade 1 Braille Text Output", f"`{braille_out.get('grade1_braille', 'N/A')}`")
                render_card("Grade 2 Braille Text Output (Contracted)", f"`{braille_out.get('grade2_braille', 'N/A')}`")
            with col_notes:
                render_card("Translation Settings & Metrics",
                    f"- **Cells Count**: {braille_out.get('character_count', 0)} cells\n"
                    f"- **Contraction Notes**: {braille_out.get('translation_notes', 'N/A')}\n"
                    f"- **Confidence score**: `{braille_out.get('confidence_score', 0.0) * 100:.1f}%`"
                )
                
            # Download file
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
                mime="text/plain"
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
            col_graphic, col_specs = st.columns([1, 1])
            
            with col_graphic:
                st.subheader("Tactile SVG Graphic")
                svg = tactile_out.get("simplified_svg", "")
                if svg:
                    try:
                        b64_svg = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
                        st.markdown(
                            f'<div style="text-align: center; background-color: #ffffff; padding: 1.5rem; border-radius: 16px; border: 2px solid #ccc; display: inline-block;">'
                            f'<img src="data:image/svg+xml;base64,{b64_svg}" style="max-height: 380px; max-width: 100%;"/>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    except Exception as e:
                        st.error(f"SVG render error: {e}")
                else:
                    st.info("SVG graphic content is empty.")
                    
                st.subheader("Exporter Options")
                st.download_button(
                    label="📐 Download Simplified SVG Outline",
                    data=svg,
                    file_name=f"tactile_outline_{st.session_state.active_run.get('uploaded_image', 'art')}.svg",
                    mime="image/svg+xml"
                )
                
                st.download_button(
                    label="🖨️ Download Embosser-Ready SVG",
                    data=tactile_out.get("embosser_ready_svg", ""),
                    file_name=f"tactile_embosser_{st.session_state.active_run.get('uploaded_image', 'art')}.svg",
                    mime="image/svg+xml"
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
        
        # Load and Cache learning package
        if not st.session_state.learning_content:
            with st.spinner("Generating personalized educational package via Gemini..."):
                key = os.getenv("GEMINI_API_KEY", "")
                st.session_state.learning_content = generate_educational_package(art_title, artist, desc, key)
                
        edu = st.session_state.learning_content
        
        st.header(f"Study Guide: {art_title}")
        
        # Display educational metrics
        render_card("📝 Artwork Summary", edu.get("summary", "N/A"))
        
        c_facts, c_vocab = st.columns(2)
        with c_facts:
            facts_list = edu.get("facts", [])
            facts_md = "\n".join([f"- {fact}" for fact in facts_list])
            render_card("💡 Did You Know? (Interesting Facts)", facts_md)
        with c_vocab:
            vocab_list = edu.get("vocabulary", [])
            vocab_md = ""
            for item in vocab_list:
                vocab_md += f"**{item.get('word')}**: {item.get('definition')}\n\n"
            render_card("📚 Vocabulary checks", vocab_md)
            
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
                    opts = q.get("options", [])
                    c_idx = q.get("correct_index", 0)
                    correct_opt = opts[c_idx] if c_idx < len(opts) else ""
                    
                    if sel == correct_opt:
                        correct += 1
                        st.success(f"**Question {idx+1}**: ✅ Correct!\n\n*Selected Option: {sel}*\n\n{q.get('explanation')}")
                    else:
                        st.error(f"**Question {idx+1}**: ❌ Incorrect.\n\n*Selected Option: {sel}*\n\n*Correct Option: {correct_opt}*\n\n{q.get('explanation')}")
                        
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
        for conv in conversations:
            # Check if image run
            is_image_run = False
            associated_art = next((art for art in saved_arts if art.source_content == conv.user_prompt), None)
            if associated_art:
                is_image_run = (associated_art.art_type == "image")
                
            col_info, col_btn = st.columns([5, 1])
            with col_info:
                icon = "🎨" if is_image_run else "⠃"
                formatted_date = conv.created_at.strftime("%Y-%m-%d %H:%M:%S")
                st.markdown(
                    f"**{icon} {conv.user_prompt or 'Analyze artwork'}**<br/>"
                    f"<small>Session ID: `{conv.session_id}` | Date: {formatted_date}</small>",
                    unsafe_allow_html=True
                )
            with col_btn:
                if st.button("📂 Load", key=f"load_log_{conv.id}", use_container_width=True):
                    with st.spinner("Loading archive workspace..."):
                        res = load_historical_run(conv.id)
                        if res:
                            st.session_state.active_run = res
                            st.session_state.quiz_answers = {}
                            st.session_state.quiz_submitted = False
                            st.session_state.learning_content = None
                            st.success(f"Workspace loaded: '{conv.user_prompt}'!")
                            st.balloons()
                        else:
                            st.error("Failed to parse historical log entry.")
            st.divider()

# 9. SETTINGS VIEW
elif selected_page == "Settings":
    st.title("⚙️ System Configuration")
    
    st.subheader("Accessibility & Visual Preferences")
    
    # Theme Selection
    theme = st.selectbox(
        "Accessibility Theme Selection",
        options=["Sleek Dark", "Clean Light", "High Contrast"],
        index=["Sleek Dark", "Clean Light", "High Contrast"].index(st.session_state.settings_theme)
    )
    if theme != st.session_state.settings_theme:
        st.session_state.settings_theme = theme
        st.rerun()
        
    # Font Size Preferences
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
        f"- **Speech buttons**: `{'Active' if speech_toggle else 'Deactivated'}`\n"
        f"- **Gemini API Configuration**: `{'Configured (Active)' if custom_key or os.getenv('GEMINI_API_KEY') else 'Empty'}`"
    )

st.divider()
st.caption("Kaggle AI Agents Capstone - BrailleArt AI Project dashboard. Powered by Gemini 2.5 Flash & FastAPI.")

"""
app.py

Streamlit Application Dashboard.
Features:
1. Interactive playground to upload images or input text.
2. Parameter adjustments (dithering threshold, dimensions) for Braille art generation.
3. Co-creative AI Chat section interacting with the Gemini 2.5 Flash agent.
4. Gallery view of previously generated and saved Braille art.
"""

import streamlit as st

st.set_page_config(
    page_title="BrailleArt AI Dashboard",
    page_icon="⠃⠗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich styling & accessibility
st.markdown("""
<style>
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(45deg, #FF4B4B, #FF8F8F);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #7f8c8d;
        margin-bottom: 2rem;
    }
    .braille-output {
        font-family: 'Courier New', Courier, monospace;
        font-size: 14px;
        line-height: 1.2;
        background-color: #1e1e1e;
        color: #00FF66;
        padding: 1.5rem;
        border-radius: 8px;
        overflow-x: auto;
        white-space: pre;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⠃⠗ BrailleArt AI Settings")
    st.write("Configure conversion parameters & Agent options below:")
    
    conversion_mode = st.selectbox(
        "Conversion Target",
        ["Text-to-Braille Translation", "Image-to-Braille Art"]
    )
    
    # Image parameter adjustments
    if conversion_mode == "Image-to-Braille Art":
        st.subheader("Image Options")
        target_width = st.slider("Target Width (cols)", 20, 150, 80)
        contrast_threshold = st.slider("Contrast Threshold", 0, 255, 128)
        dither = st.checkbox("Apply Floyd-Steinberg Dithering", value=True)
    
    st.divider()
    st.info("Kaggle AI Agents: Capstone Project (Agents for Good track)")

# Main Layout
st.markdown('<div class="main-title">BrailleArt AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Accessible AI agents converting visual ideas and images into tactile Braille representation</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🎨 Generator Studio", "💬 Agent Chat Workspace", "📚 Gallery & Audits"])

with tab1:
    st.header("Tactile Generator Studio")
    if conversion_mode == "Text-to-Braille Translation":
        user_text = st.text_area("Enter Text to translate into Braille unicode:", value="Hello World")
        if st.button("Translate Text"):
            st.info("Invoking translation tool backend (placeholder)...")
            st.markdown('<div class="braille-output">⠠⠓⠑⠇⠇⠕ ⠠⠺⠕⠗⠇⠙</div>', unsafe_allow_html=True)
            
    else:
        uploaded_file = st.file_uploader("Upload an Image to render as Braille Art", type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.image(uploaded_file, caption="Source Image", use_column_width=True)
            with col2:
                st.write("Generated Braille Art Preview:")
                # Placeholder Braille art rendering a circle or box
                dummy_braille = """
⠀⠀⠀⠀⠀⠀⣀⣤⣴⣶⣶⣾⣿⣿⣷⣶⣶⣤⣀⡀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀⠀⠀⠀
⠀⠀⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⠀
⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀⠀
⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀
⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀
⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀⠀
⠀⠀⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⠀
⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠉⠛⠻⠿⠿⣿⣿⣿⣿⠿⠿⠛⠋⠉⠀⠀⠀⠀⠀⠀
                """
                st.markdown(f'<div class="braille-output">{dummy_braille}</div>', unsafe_allow_html=True)

with tab2:
    st.header("Co-Creative Agent Workspace")
    st.write("Discuss concepts with the BrailleArt agent. The agent can adjust parameters, describe tactile layouts, and explain visual contexts.")
    
    # Simple chat container
    chat_container = st.container()
    with chat_container:
        st.chat_message("assistant").write("Hello! I am your BrailleArt Agent assistant. Upload an image or tell me what tactile pattern you'd like to draft.")
        
    chat_input = st.chat_input("Ask me to generate a tactical map, a simple shape, or translate a visual object.")
    if chat_input:
        st.chat_message("user").write(chat_input)
        st.chat_message("assistant").write("Agent reasoning in progress (placeholder)...")

with tab3:
    st.header("Saved Gallery & Audit Logs")
    st.write("Browse historical Braille art designs and see verification/audit trails for accessible outputs.")
    
    # Placeholder database table
    st.table([
        {"ID": 1, "Type": "Text", "Source": "Hello World", "Created At": "2026-06-26 01:00:00"},
        {"ID": 2, "Type": "Image", "Source": "circle.png", "Created At": "2026-06-26 01:05:00"}
    ])
st.divider()
st.caption("Powered by Gemini 2.5 Flash & Google Gen AI ADK")

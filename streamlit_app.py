import streamlit as st
import json
import os
import re
from datetime import datetime
from suno_expert import generate_suno_prompt, validate_suno_tags, MAX_MODE_TAGS, SUNO_STRUCTURE_TAGS

# Page config
st.set_page_config(
    page_title="🎵 Suno Max Pro",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Detect if running on Streamlit Cloud
IS_CLOUD = "STREAMLIT_RUNTIME" in os.environ

# Custom CSS
st.markdown("""
<style>
    .stApp {background: #020204;}
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div {
        background: rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.1); color: #e2e8f0; border-radius: 1rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #06b6d4, #3b82f6); color: white; border: none; border-radius: 1.5rem;
        font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; padding: 0.75rem 1.5rem;
    }
    .stButton > button:hover {transform: scale(1.02); box-shadow: 0 10px 25px -5px rgba(6,182,212,0.3);}
    .success-box {background: rgba(34,197,94,0.1); border-left: 4px solid #22c55e; padding: 1rem; border-radius: 0.5rem;}
    .error-box {background: rgba(239,68,68,0.1); border-left: 4px solid #ef4444; padding: 1rem; border-radius: 0.5rem;}
    .tag-badge {background: rgba(6,182,212,0.1); border: 1px solid rgba(6,182,212,0.3); color: #67e8f9; padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 700;}
</style>
""", unsafe_allow_html=True)

# Session state
if "result" not in st.session_state:
    st.session_state.result = None

# Sidebar
with st.sidebar:
    st.title("⚙️ Config")
    
    # Backend Selector
    available_backends = ["gemini", "huggingface"]
    if not IS_CLOUD:
        available_backends.insert(0, "ollama")  # Only show Ollama on local Mac
    
    backend = st.selectbox("🤖 AI Backend", available_backends, index=0)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        language = st.text_input("🌐 Language", value="Spanish")
        bpm = st.text_input("🎯 BPM", value="AUTO")
    with col2:
        duration = st.text_input("⏱️ Duration", value="2:30min")
        vocal_type = st.selectbox("🎤 Vocal Type", ["Male", "Female", "Duet", "Choir", "Kids"])
    
    genre = st.text_input("🎸 Genre or Artist", placeholder="e.g., Rosalía, Synthwave")
    topic = st.text_area("💭 Creative Prompt", placeholder="Describe theme...", height=100)
    
    col_a, col_b = st.columns(2)
    with col_a:
        max_mode = st.toggle("⚡ MAX Mode", value=True)
    with col_b:
        vocal_directing = st.toggle("🎙️ Pro Vocals", value=True)
    
    st.divider()
    generate_btn = st.button("🚀 Generate", type="primary", use_container_width=True)
    
    # Status Badge
    if backend == "ollama":
        st.markdown('<div class="tag-badge" style="background:rgba(34,197,94,0.2);border-color:#22c55e;color:#86efac">🟢 Local (M4)</div>', unsafe_allow_html=True)
    elif backend == "gemini":
        st.markdown('<div class="tag-badge" style="background:rgba(59,130,246,0.2);border-color:#3b82f6;color:#93c5fd">🔵 Cloud API</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="tag-badge" style="background:rgba(168,85,247,0.2);border-color:#a855f7;color:#d8b4fe">🟣 Free Tier</div>', unsafe_allow_html=True)

# Main
st.title("🎵 Suno Max Pro")
st.markdown("*Expert AI prompt generator • Tag-validated • Cloud Ready*")

if st.session_state.result:
    result = st.session_state.result
    if result.get("error"):
        st.error(f"❌ {result['error']}")
    else:
        st.markdown(f"""<div class="success-box">
            ✅ Generated with <strong>{result['backend_used'].upper()}</strong>
            • Title: <strong>{result['title']}</strong>
        </div>""", unsafe_allow_html=True)
        
        col_style, col_lyrics = st.columns(2)
        with col_style:
            st.markdown("### 🎛️ Style Prompt")
            st.code(result["style_prompt"], language="text")
            st.caption("💡 Copy to Suno's *Style of Music* field")
        with col_lyrics:
            st.markdown("### 📝 Lyrics & Tags")
            st.text_area("Lyrics", value=result["lyrics"], height=300)
            st.caption("💡 Copy to Suno's *Lyrics* field")
        
        st.divider()
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            prompt_content = f"""🎵 SUNO AI PROMPT - {result['title']}
━━━━━━━━━━━━━━━━━━━━━━
🔹 STYLE:
{result['style_prompt']}

🔹 LYRICS:
{result['lyrics']}
"""
            st.download_button("📄 Download Prompt", data=prompt_content, file_name=f"{result['title']}_prompt.txt", mime="text/plain", use_container_width=True)
        with col_exp2:
            st.info("📋 To copy: Click text → Cmd+A → Cmd+C")

if generate_btn:
    if not genre or not topic:
        st.error("⚠️ Please fill in *Genre* and *Creative Prompt*")
    else:
        with st.spinner(f"🤖 Generating with {backend.upper()}..."):
            config = {
                "genre": genre, "topic": topic, "language": language,
                "vocalType": vocal_type, "bpm": bpm, "duration": duration
            }
            result = generate_suno_prompt(config, max_mode, vocal_directing)
            st.session_state.result = result
            st.rerun()

st.divider()
st.markdown('<div style="text-align: center; color: #64748b; font-size: 0.75rem;">🎵 Made for Altea • Cloud Edition</div>', unsafe_allow_html=True)

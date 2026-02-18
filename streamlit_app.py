import streamlit as st
import json
import os
import re
from datetime import datetime
from suno_expert import generate_suno_prompt, validate_suno_tags, MAX_MODE_TAGS

# Page config
st.set_page_config(page_title="🎵 Suno Max Pro", page_icon="🎵", layout="wide")

# 🔧 HARDCODED: Use Hugging Face backend (no dropdown confusion)
BACKEND = "huggingface"

# Custom CSS
st.markdown("""
<style>
    .stApp {background: #020204;}
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background: rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.1); 
        color: #e2e8f0; border-radius: 1rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #06b6d4, #3b82f6); color: white; 
        border: none; border-radius: 1.5rem; font-weight: 800; 
        text-transform: uppercase; letter-spacing: 0.05em;
    }
    .success-box {background: rgba(34,197,94,0.1); border-left: 4px solid #22c55e; 
                  padding: 1rem; border-radius: 0.5rem;}
    .error-box {background: rgba(239,68,68,0.1); border-left: 4px solid #ef4444; 
                padding: 1rem; border-radius: 0.5rem;}
</style>
""", unsafe_allow_html=True)

# Session state
if "result" not in st.session_state:
    st.session_state.result = None

# Sidebar
with st.sidebar:
    st.title("⚙️ Config")
    
    # 🔧 Backend badge (hardcoded)
    st.markdown('<div style="background:rgba(168,85,247,0.2);border:1px solid #a855f7;color:#d8b4fe;padding:0.25rem 0.75rem;border-radius:1rem;font-size:0.75rem;font-weight:700">🟣 Backend: Hugging Face</div>', unsafe_allow_html=True)
    
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
    
    # Token status
    hf_token = os.getenv("HF_API_TOKEN")
    if hf_token:
        st.markdown('<div style="color:#22c55e;font-size:0.75rem">✅ HF Token: Loaded</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#ef4444;font-size:0.75rem">❌ HF Token: Missing</div>', unsafe_allow_html=True)

# Main
st.title("🎵 Suno Max Pro")
st.markdown("*Expert AI prompt generator • Hugging Face Backend • Tag-Validated*")

# Results
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
            st.download_button("📄 Download Prompt", data=prompt_content, 
                             file_name=f"{result['title']}_prompt.txt", 
                             mime="text/plain", use_container_width=True)
        with col_exp2:
            st.info("📋 To copy: Click text → Cmd+A → Cmd+C")

# Generate logic
if generate_btn:
    if not genre or not topic:
        st.error("⚠️ Please fill in *Genre* and *Creative Prompt*")
    else:
        with st.spinner(f"🤖 Generating with {BACKEND.upper()}..."):
            config = {
                "genre": genre, "topic": topic, "language": language,
                "vocalType": vocal_type, "bpm": bpm, "duration": duration
            }
            result = generate_suno_prompt(config, max_mode, vocal_directing)
            st.session_state.result = result
            st.rerun()

# Footer
st.divider()
st.markdown('<div style="text-align: center; color: #64748b; font-size: 0.75rem;">🎵 Made for Altea • HF Backend</div>', unsafe_allow_html=True)

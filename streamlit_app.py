import streamlit as st
import json
import os
import re
import time
from datetime import datetime
from suno_expert import generate_suno_prompt, validate_suno_tags, MAX_MODE_TAGS

st.set_page_config(page_title="🎵 Suno Max Pro", page_icon="🎵", layout="wide")

# ===== CLEAN, HIGH-CONTRAST CSS =====
st.markdown("""
<style>
    /* Background */
    .stApp {background: #0a0a12;}
    
    /* Text - HIGH CONTRAST */
    .stMarkdown, .stText, .stTextInput, .stSelectbox, .stTextArea {color: #ffffff !important;}
    label {color: #e0e0e0 !important; font-weight: 600 !important;}
    
    /* Input fields */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div > select {
        background: #1a1a25 !important; border: 1px solid #404055 !important;
        color: #ffffff !important; border-radius: 6px !important; padding: 12px !important; font-size: 15px !important;
    }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: #7c3aed !important; box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.3) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: #7c3aed !important; color: #ffffff !important; border: none !important;
        border-radius: 6px !important; padding: 12px 20px !important; font-size: 14px !important; font-weight: 600 !important;
    }
    .stButton > button:hover {background: #8b5cf6 !important; transform: translateY(-1px) !important;}
    
    /* Code blocks - LARGE and READABLE */
    .stCode {background: #1a1a25 !important; border: 1px solid #404055 !important; border-radius: 8px !important;}
    .stCode code {color: #ffffff !important; font-size: 14px !important; line-height: 1.8 !important; font-family: 'Courier New', monospace !important;}
    
    /* Text areas for output */
    .stTextArea label {color: #a78bfa !important; font-size: 14px !important; font-weight: 700 !important;}
    
    /* Sidebar */
    [data-testid="stSidebar"] {background: #0f0f1a !important; border-right: 1px solid #2a2a35 !important;}
    
    /* Headers */
    h1 {color: #ffffff !important; font-size: 32px !important; font-weight: 700 !important;}
    h2 {color: #ffffff !important; font-size: 24px !important; font-weight: 600 !important;}
    h3 {color: #c4b5fd !important; font-size: 18px !important; font-weight: 600 !important;}
    
    /* Success/Error boxes */
    .success-box {background: rgba(34, 197, 94, 0.15) !important; border-left: 4px solid #22c55e !important;
        padding: 16px !important; border-radius: 6px !important; color: #86efac !important; margin: 16px 0 !important;}
    .error-box {background: rgba(239, 68, 68, 0.15) !important; border-left: 4px solid #ef4444 !important;
        padding: 16px !important; border-radius: 6px !important; color: #fca5a5 !important; margin: 16px 0 !important;}
    
    /* Copy button feedback */
    .copy-success {background: rgba(34, 197, 94, 0.3) !important; color: #86efac !important;}
    
    /* Badges */
    .badge {display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; margin: 4px 0;}
    .badge-groq {background: rgba(124, 58, 237, 0.25); color: #c4b5fd; border: 1px solid #7c3aed;}
    .badge-success {background: rgba(34, 197, 94, 0.25); color: #86efac; border: 1px solid #22c55e;}
    
    /* Dividers */
    hr {border-color: #2a2a35 !important; margin: 20px 0 !important;}
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Session state
if "result" not in st.session_state:
    st.session_state.result = None
if "copied_field" not in st.session_state:
    st.session_state.copied_field = None

# ===== SIDEBAR =====
with st.sidebar:
    st.title("⚙️ Settings")
    st.markdown('<span class="badge badge-groq">🔵 Groq + Web Search</span>', unsafe_allow_html=True)
    st.divider()
    
    st.markdown("### 📝 Song Details")
    col1, col2 = st.columns(2)
    with col1:
        language = st.text_input("Language", value="Spanish", key="inp_lang")
        bpm = st.text_input("BPM", value="AUTO", key="inp_bpm")
    with col2:
        duration = st.text_input("Duration", value="2:30min", key="inp_dur")
        vocal_type = st.selectbox("Vocal Type", ["Male", "Female", "Duet", "Choir", "Kids"], key="inp_vocal")
    
    genre = st.text_input("🎸 Genre or Artist", placeholder="e.g., The Weeknd, Rosalía...", key="inp_genre")
    topic = st.text_area("💭 Creative Prompt", placeholder="Describe theme, story, or mood...", height=70, key="inp_topic")
    
    st.divider()
    st.markdown("### ⚡ Options")
    max_mode = st.toggle("⚡ MAX Mode", value=True, key="opt_max", help="Add professional quality tags")
    vocal_directing = st.toggle("🎙️ Pro Vocals", value=True, key="opt_vocal", 
        help="ON: Detailed vocal tags per section/line | OFF: Basic structure tags only")
    
    st.divider()
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        st.markdown('<span class="badge badge-success">✅ API Ready</span>', unsafe_allow_html=True)
    
    generate_btn = st.button("🚀 Generate", type="primary", use_container_width=True, key="btn_generate")

# ===== MAIN CONTENT =====
st.title("🎵 Suno Max Pro")
st.markdown("*AI prompt generator with Web Research • v6.0*")

st.divider()

# ===== RESULTS =====
if st.session_state.result:
    result = st.session_state.result
    
    if result.get("error"):
        st.markdown(f'<div class="error-box">❌ <strong>Error:</strong> {result["error"]}</div>', unsafe_allow_html=True)
    else:
        # Research status
        if result.get("search_status"):
            st.info(f"🔍 {result['search_status']} | Pro Vocals: {'✅ ON' if result.get('vocal_directing_used') else '❌ OFF'}")
        
        st.markdown(f'''<div class="success-box">
            ✅ <strong>Generated!</strong> | Backend: {result["backend_used"].upper()} | 
            Research: {"✅ Used" if result.get("research_used") else "❌ Skipped"}
        </div>''', unsafe_allow_html=True)
        
        # ===== TITLE FIELD (Editable) =====
        st.markdown("### 🏷️ Song Title")
        col_title1, col_title2 = st.columns([5, 1])
        with col_title1:
            edited_title = st.text_input("Title (editable)", value=result["title"], key="edit_title", label_visibility="collapsed")
        with col_title2:
            if st.button("📋 Copy", key="copy_title", use_container_width=True):
                st.session_state.copied_field = "title"
                st.rerun()
        
        if st.session_state.copied_field == "title":
            st.success("✅ Title copied to clipboard!")
            st.session_state.copied_field = None
        
        # ===== TWO COLUMN LAYOUT =====
        col_style, col_lyrics = st.columns(2)
        
        # Style Prompt
        with col_style:
            st.markdown("### 🎛️ Style Prompt")
            st.caption("Paste in Suno's *Style of Music* field")
            st.code(result["style_prompt"], language="text", line_numbers=False)
            st.caption(f"📊 {len(result['style_prompt'])} characters")
            
            if st.button("📋 Copy Style", key="copy_style", use_container_width=True):
                st.session_state.copied_field = "style"
                st.rerun()
            if st.session_state.copied_field == "style":
                st.success("✅ Style prompt copied!")
                st.session_state.copied_field = None
        
        # Lyrics
        with col_lyrics:
            st.markdown("### 📝 Lyrics & Tags")
            st.caption("Paste in Suno's *Lyrics* field (Custom Mode)")
            st.text_area("Lyrics", value=result["lyrics"], height=380, key="txt_lyrics", label_visibility="collapsed")
            
            if st.button("📋 Copy Lyrics", key="copy_lyrics", use_container_width=True):
                st.session_state.copied_field = "lyrics"
                st.rerun()
            if st.session_state.copied_field == "lyrics":
                st.success("✅ Lyrics copied!")
                st.session_state.copied_field = None
        
        st.divider()
        
        # ===== EXPORT =====
        st.markdown("### 💾 Export")
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            prompt_content = f"""SUNO AI PROMPT - {edited_title}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*60}

STYLE PROMPT:
{result['style_prompt']}

LYRICS:
{result['lyrics']}
"""
            st.download_button("📄 Download Full", data=prompt_content,
                file_name=f"{edited_title.lower().replace(' ', '_')}_prompt.txt",
                mime="text/plain", use_container_width=True)
        
        with col_exp2:
            # CLEAN lyrics - NO vocal tags, NO header
            clean = result['lyrics']
            clean = re.sub(r'\[Style:.*?\]\n?', '', clean)
            clean = re.sub(r'\[Duration:.*?\]\n?', '', clean)
            clean = re.sub(r'\[BPM:.*?\]\n?', '', clean)
            clean = re.sub(r'\[Is_MAX_MODE:.*?\]\n?', '', clean)
            clean = re.sub(r'\[QUALITY:.*?\]\n?', '', clean)
            clean = re.sub(r'\[REALISM:.*?\]\n?', '', clean)
            clean = re.sub(r'\[REAL_INSTRUMENTS:.*?\]\n?', '', clean)
            clean = re.sub(r'\[AUDIO_SPEC:.*?\]\n?', '', clean)
            clean = re.sub(r'\[PRODUCTION:.*?\]\n?', '', clean)
            # Remove vocal tags but keep structure
            clean = re.sub(r'\[(Male|Female|Duet|Choir|Kids) Vocal\]\s*\n?', '', clean)
            clean = re.sub(r'\[(Breathy|Powerful|Soft|Clear|Intimate|Emotional)\]\s*\n?', '', clean)
            clean = re.sub(r'\[(Reverb|Delay|Wide Stereo|Centered|Harmonies)\]\s*\n?', '', clean)
            # Remove expression parentheses
            clean = re.sub(r'\([^)]*\)', '', clean)
            
            # NO header - just clean lyrics
            lyrics_content = clean.strip()
            
            st.download_button("📄 Download Clean", data=lyrics_content,
                file_name=f"{edited_title.lower().replace(' ', '_')}_lyrics.txt",
                mime="text/plain", use_container_width=True)

# ===== GENERATE ACTION =====
if generate_btn:
    if not genre or not topic:
        st.markdown('<div class="error-box">⚠️ Fill in <em>Genre/Artist</em> and <em>Creative Prompt</em></div>', unsafe_allow_html=True)
    else:
        is_artist = len(genre.split()) > 1 and any(c.isupper() for c in genre)
        
        if is_artist:
            with st.status("🔍 Researching artist...", expanded=True) as status:
                st.write("Searching production details...")
                time.sleep(0.3)
                st.write("Analyzing vocal style...")
                time.sleep(0.3)
                
                config = {"genre": genre, "topic": topic, "language": language,
                    "vocalType": vocal_type, "bpm": bpm, "duration": duration}
                result = generate_suno_prompt(config, max_mode, vocal_directing)
                st.session_state.result = result
                
                status.update(label="✅ Complete!" if result.get("success") else "❌ Failed",
                    state="complete" if result.get("success") else "error")
        else:
            with st.spinner("🤖 Generating..."):
                config = {"genre": genre, "topic": topic, "language": language,
                    "vocalType": vocal_type, "bpm": bpm, "duration": duration}
                result = generate_suno_prompt(config, max_mode, vocal_directing)
                st.session_state.result = result
        
        st.rerun()

# ===== FOOTER =====
st.divider()
st.markdown('<div style="text-align: center; color: #505060; font-size: 12px; padding: 20px;">🎵 Suno Max Pro v6.0 • Made for Altea</div>', unsafe_allow_html=True)

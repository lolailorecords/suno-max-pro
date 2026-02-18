import streamlit as st
import json
import os
import re
import time
from datetime import datetime
from suno_expert import generate_suno_prompt, validate_suno_tags, MAX_MODE_TAGS

# Page config
st.set_page_config(
    page_title="🎵 Suno Max Pro",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Clean, Readable, Professional
st.markdown("""
<style>
    .stApp {background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);}
    .stMarkdown, .stText, .stNumberInput, .stTextInput, .stSelectbox {color: #e8e8e8 !important;}
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div > select {
        background: #1e1e2f !important; border: 1px solid #3a3a5c !important;
        color: #ffffff !important; border-radius: 8px !important; padding: 10px !important; font-size: 14px !important;
    }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: #6366f1 !important; box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important; color: #ffffff !important;
        border: none !important; border-radius: 8px !important; padding: 12px 24px !important;
        font-size: 14px !important; font-weight: 600 !important; cursor: pointer !important;
    }
    .stButton > button:hover {transform: translateY(-1px) !important; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4) !important;}
    .success-box {background: rgba(34, 197, 94, 0.15) !important; border-left: 4px solid #22c55e !important;
        padding: 16px !important; border-radius: 8px !important; color: #86efac !important; margin: 16px 0 !important;}
    .error-box {background: rgba(239, 68, 68, 0.15) !important; border-left: 4px solid #ef4444 !important;
        padding: 16px !important; border-radius: 8px !important; color: #fca5a5 !important; margin: 16px 0 !important;}
    .stCode {background: #1e1e2f !important; border: 1px solid #3a3a5c !important; border-radius: 8px !important;}
    .stCode code {color: #e8e8e8 !important; font-size: 13px !important; line-height: 1.6 !important;}
    [data-testid="stSidebar"] {background: #16162a !important; border-right: 1px solid #3a3a5c !important;}
    h1, h2, h3 {color: #ffffff !important; font-weight: 600 !important;}
    h1 {font-size: 28px !important;} h2 {font-size: 22px !important;} h3 {font-size: 18px !important;}
    .badge {display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin: 4px 0;}
    .badge-groq {background: rgba(99, 102, 241, 0.2); color: #a5b4fc; border: 1px solid #6366f1;}
    .badge-success {background: rgba(34, 197, 94, 0.2); color: #86efac; border: 1px solid #22c55e;}
    .tag-example {background: rgba(99, 102, 241, 0.15); border: 1px dashed #6366f1;
        padding: 6px 10px; border-radius: 6px; font-family: monospace; font-size: 12px; color: #c7d2fe; margin: 4px 0; display: inline-block;}
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Session state
if "result" not in st.session_state:
    st.session_state.result = None
if "last_config" not in st.session_state:
    st.session_state.last_config = {}

# ============== SIDEBAR ==============
with st.sidebar:
    st.title("⚙️ Configuration")
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
    
    genre = st.text_input("Genre or Artist", placeholder="e.g., The Weeknd, Rosalía, Bohemian Rhapsody...", key="inp_genre")
    topic = st.text_area("Creative Prompt", placeholder="Describe theme, story, or mood...", height=80, key="inp_topic")
    
    st.divider()
    st.markdown("### ⚡ Options")
    max_mode = st.toggle("MAX Mode", value=True, key="opt_max")
    vocal_directing = st.toggle("Pro Vocals", value=True, key="opt_vocal")
    
    st.divider()
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        st.markdown('<span class="badge badge-success">✅ API Key: Ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge">⚠️ API Key: Missing</span>', unsafe_allow_html=True)
    
    # ✅ DEFINE BUTTON FIRST (before checking it)
    generate_btn = st.button("🚀 Generate Prompt", type="primary", use_container_width=True, key="btn_generate")

# ============== MAIN CONTENT ==============
st.title("🎵 Suno Max Pro")
st.markdown("*Professional AI prompt generator with Web Research*")

with st.expander("📚 Suno Tag Reference"):
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.markdown("**Structure**")
        for tag in ["Intro", "Verse", "Chorus", "Bridge", "Outro"]:
            st.markdown(f'<span class="tag-example">[{tag}]</span>', unsafe_allow_html=True)
    with col_t2:
        st.markdown("**Vocals**")
        for tag in ["Male Vocal", "Female Vocal", "Breathy", "Powerful"]:
            st.markdown(f'<span class="tag-example">[{tag}]</span>', unsafe_allow_html=True)
    with col_t3:
        st.markdown("**Effects**")
        for tag in ["Reverb", "Delay", "Wide Stereo", "AutoTune"]:
            st.markdown(f'<span class="tag-example">[{tag}]</span>', unsafe_allow_html=True)

st.divider()

# ============== RESULTS SECTION ==============
if st.session_state.result:
    result = st.session_state.result
    
    if result.get("error"):
        st.markdown(f'<div class="error-box">❌ <strong>Error:</strong> {result["error"]}</div>', unsafe_allow_html=True)
    else:
        # Show research status if available
        if result.get("search_status"):
            st.info(f"🔍 {result['search_status']}")
        
        st.markdown(f'''<div class="success-box">
            ✅ <strong>Generated Successfully!</strong> | 
            Backend: {result["backend_used"].upper()} | 
            Title: <em>{result["title"]}</em> |
            Research: {"✅ Used" if result.get("research_used") else "❌ Skipped (generic genre)"}
        </div>''', unsafe_allow_html=True)
        
        col_style, col_lyrics = st.columns(2)
        
        with col_style:
            st.markdown("### 🎛️ Style Prompt")
            st.markdown("*Copy to Suno's \"Style of Music\" field*")
            st.code(result["style_prompt"], language="text", line_numbers=False)
            char_count = len(result["style_prompt"])
            st.caption(f"📊 {char_count} characters")
        
        with col_lyrics:
            st.markdown("### 📝 Lyrics & Tags")
            st.markdown("*Copy to Suno's \"Lyrics\" field (Custom Mode)*")
            st.text_area("Lyrics Output", value=result["lyrics"], height=350, key="txt_lyrics", label_visibility="collapsed")
        
        st.divider()
        st.markdown("### 💾 Export")
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            prompt_content = f"""SUNO AI PROMPT - {result['title']}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*50}

STYLE PROMPT:
{result['style_prompt']}

LYRICS & TAGS:
{result['lyrics']}
"""
            st.download_button("📄 Download Full Prompt", data=prompt_content,
                file_name=f"{result['title'].lower().replace(' ', '_')}_prompt.txt",
                mime="text/plain", use_container_width=True)
        
        with col_exp2:
            clean_lyrics = re.sub(r'\[Style:.*?\]\n?', '', result['lyrics'])
            clean_lyrics = re.sub(r'\[Duration:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[BPM:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[Is_MAX_MODE:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[QUALITY:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[(Male|Female|Duet|Choir|Kids) Vocal\]\s*', '', clean_lyrics)
            
            lyrics_content = f"""CLEAN LYRICS - {result['title']}
{'='*50}

{clean_lyrics.strip()}
"""
            st.download_button("📄 Download Clean Lyrics", data=lyrics_content,
                file_name=f"{result['title'].lower().replace(' ', '_')}_lyrics.txt",
                mime="text/plain", use_container_width=True)

# ============== GENERATE ACTION (AFTER button is defined) ==============
if generate_btn:
    if not genre or not topic:
        st.markdown('<div class="error-box">⚠️ <strong>Missing Input:</strong> Please fill in both <em>Genre/Artist</em> and <em>Creative Prompt</em> fields</div>', unsafe_allow_html=True)
    else:
        # Check if it looks like an artist/song name (for search progress display)
        is_artist_like = len(genre.split()) > 1 and any(c.isupper() for c in genre)
        
        if is_artist_like:
            with st.status("🔍 Researching artist style on the web...", expanded=True) as status:
                st.write("Searching for production details...")
                time.sleep(0.5)
                st.write("Analyzing vocal techniques...")
                time.sleep(0.5)
                st.write("Generating detailed prompt...")
                
                config = {
                    "genre": genre, "topic": topic, "language": language,
                    "vocalType": vocal_type, "bpm": bpm, "duration": duration
                }
                
                result = generate_suno_prompt(config, max_mode, vocal_directing)
                st.session_state.result = result
                st.session_state.last_config = config
                
                if result.get("success"):
                    status.update(label="✅ Research & Generation Complete!", state="complete")
                else:
                    status.update(label="❌ Generation Failed", state="error")
        else:
            with st.spinner("🤖 Generating with Groq..."):
                config = {
                    "genre": genre, "topic": topic, "language": language,
                    "vocalType": vocal_type, "bpm": bpm, "duration": duration
                }
                result = generate_suno_prompt(config, max_mode, vocal_directing)
                st.session_state.result = result
                st.session_state.last_config = config
        
        st.rerun()

# ============== FOOTER ==============
st.divider()
st.markdown('<div style="text-align: center; color: #6b7280; font-size: 12px; padding: 20px 0;">🎵 Suno Max Pro v6.0 • Web Search Enabled • Made for Altea</div>', unsafe_allow_html=True)

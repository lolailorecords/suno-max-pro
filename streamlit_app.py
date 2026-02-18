import streamlit as st
import json
import os
import re
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
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
    }
    
    /* Better text readability */
    .stMarkdown, .stText, .stNumberInput, .stTextInput, .stSelectbox {
        color: #e8e8e8 !important;
    }
    
    /* Input fields - clean and readable */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {
        background: #1e1e2f !important;
        border: 1px solid #3a3a5c !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        padding: 10px !important;
        font-size: 14px !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
    }
    
    /* Buttons - clear and clickable */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4) !important;
    }
    
    .stButton > button:disabled {
        background: #3a3a5c !important;
        cursor: not-allowed !important;
    }
    
    /* Success/Error boxes - clear visibility */
    .success-box {
        background: rgba(34, 197, 94, 0.15) !important;
        border-left: 4px solid #22c55e !important;
        padding: 16px !important;
        border-radius: 8px !important;
        color: #86efac !important;
        margin: 16px 0 !important;
    }
    
    .error-box {
        background: rgba(239, 68, 68, 0.15) !important;
        border-left: 4px solid #ef4444 !important;
        padding: 16px !important;
        border-radius: 8px !important;
        color: #fca5a5 !important;
        margin: 16px 0 !important;
    }
    
    /* Code blocks - readable output */
    .stCode {
        background: #1e1e2f !important;
        border: 1px solid #3a3a5c !important;
        border-radius: 8px !important;
    }
    
    .stCode code {
        color: #e8e8e8 !important;
        font-size: 13px !important;
        line-height: 1.6 !important;
    }
    
    /* Text areas for output - large and readable */
    .stTextArea label {
        color: #a5b4fc !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }
    
    /* Sidebar - clean organization */
    [data-testid="stSidebar"] {
        background: #16162a !important;
        border-right: 1px solid #3a3a5c !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e8e8e8 !important;
    }
    
    /* Headers - clear hierarchy */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    h1 { font-size: 28px !important; margin-bottom: 8px !important; }
    h2 { font-size: 22px !important; margin-bottom: 12px !important; }
    h3 { font-size: 18px !important; margin-bottom: 8px !important; }
    
    /* Labels - readable */
    .stMarkdown label, .stTextInput label, .stSelectbox label {
        color: #c7d2fe !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        margin-bottom: 4px !important;
    }
    
    /* Toggle switches */
    .stCheckbox label {
        color: #e8e8e8 !important;
        font-weight: 500 !important;
    }
    
    /* Divider lines */
    hr {
        border-color: #3a3a5c !important;
        margin: 20px 0 !important;
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: #1e1e2f !important;
        border: 1px solid #3a3a5c !important;
        color: #a5b4fc !important;
        border-radius: 6px !important;
    }
    
    .stDownloadButton > button:hover {
        border-color: #6366f1 !important;
        color: #ffffff !important;
    }
    
    /* Info/Warning boxes */
    .stAlert {
        border-radius: 8px !important;
        border: none !important;
    }
    
    /* Expander - clean */
    .streamlit-expanderHeader {
        background: #1e1e2f !important;
        border: 1px solid #3a3a5c !important;
        border-radius: 8px !important;
        color: #e8e8e8 !important;
    }
    
    /* Badge styles */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin: 4px 0;
    }
    .badge-groq { background: rgba(99, 102, 241, 0.2); color: #a5b4fc; border: 1px solid #6366f1; }
    .badge-success { background: rgba(34, 197, 94, 0.2); color: #86efac; border: 1px solid #22c55e; }
    .badge-warning { background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid #f59e0b; }
    
    /* Tag examples */
    .tag-example {
        background: rgba(99, 102, 241, 0.15);
        border: 1px dashed #6366f1;
        padding: 6px 10px;
        border-radius: 6px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        color: #c7d2fe;
        margin: 4px 0;
        display: inline-block;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
    
    # Backend status badge
    st.markdown('<span class="badge badge-groq">🔵 Groq Cloud Backend</span>', unsafe_allow_html=True)
    
    st.divider()
    
    # --- Input Section ---
    st.markdown("### 📝 Song Details")
    
    col1, col2 = st.columns(2)
    with col1:
        language = st.text_input("Language", value="Spanish", key="inp_lang")
        bpm = st.text_input("BPM", value="AUTO", key="inp_bpm", help="Enter number or AUTO")
    
    with col2:
        duration = st.text_input("Duration", value="2:30min", key="inp_dur")
        vocal_type = st.selectbox("Vocal Type", ["Male", "Female", "Duet", "Choir", "Kids"], key="inp_vocal")
    
    genre = st.text_input(
        "Genre or Artist", 
        placeholder="e.g., Rosalía, Synthwave, Jazz...", 
        key="inp_genre",
        help="Artist names trigger production-style analysis"
    )
    
    topic = st.text_area(
        "Creative Prompt", 
        placeholder="Describe the theme, story, or mood...", 
        height=80,
        key="inp_topic"
    )
    
    st.divider()
    
    # --- Options Section ---
    st.markdown("### ⚡ Options")
    
    max_mode = st.toggle("MAX Mode", value=True, key="opt_max", help="Add professional quality tags")
    vocal_directing = st.toggle("Pro Vocals", value=True, key="opt_vocal", help="Add detailed vocal direction tags")
    
    st.divider()
    
    # --- Pro Vocals Help ---
    if vocal_directing:
        with st.expander("🎤 Pro Vocals Guide"):
            st.markdown("""
            **Section Tags** (before each section):
            - `[Female Vocal] [Breathy] [Verse 1]`
            - `[Male Vocal] [Powerful] [Chorus]`
            
            **Expression Tags** (in lyrics):
            - `(soft whisper)` `(building intensity)`
            - `(powerful belt)` `(harmonies enter)`
            """)
    
    # --- API Status ---
    st.divider()
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        st.markdown('<span class="badge badge-success">✅ API Key: Ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-warning">⚠️ API Key: Missing</span>', unsafe_allow_html=True)
    
    # Generate button
    st.divider()
    generate_btn = st.button("🚀 Generate Prompt", type="primary", use_container_width=True, key="btn_generate")

# ============== MAIN CONTENT ==============
st.title("🎵 Suno Max Pro")
st.markdown("*Professional AI prompt generator for Suno AI v4*")

# --- Tag Reference (Collapsible) ---
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
        # Success banner
        st.markdown(f'''<div class="success-box">
            ✅ <strong>Generated Successfully!</strong> | 
            Backend: {result["backend_used"].upper()} | 
            Title: <em>{result["title"]}</em>
        </div>''', unsafe_allow_html=True)
        
        # Two-column output
        col_style, col_lyrics = st.columns(2)
        
        with col_style:
            st.markdown("### 🎛️ Style Prompt")
            st.markdown("*Copy to Suno's \"Style of Music\" field*")
            st.code(result["style_prompt"], language="text", line_numbers=False)
            
            # Stats
            char_count = len(result["style_prompt"])
            st.caption(f"📊 {char_count} characters")
        
        with col_lyrics:
            st.markdown("### 📝 Lyrics & Tags")
            st.markdown("*Copy to Suno's \"Lyrics\" field (Custom Mode)*")
            st.text_area(
                "Lyrics Output",
                value=result["lyrics"],
                height=350,
                key="txt_lyrics",
                label_visibility="collapsed"
            )
        
        st.divider()
        
        # Export buttons
        st.markdown("### 💾 Export")
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            prompt_content = f"""SUNO AI PROMPT - {result['title']}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*50}

STYLE PROMPT:
{result['style_prompt']}

LYRICS & TAGS:
{result['lyrics']}
"""
            st.download_button(
                "📄 Download Full Prompt",
                data=prompt_content,
                file_name=f"{result['title'].lower().replace(' ', '_')}_prompt.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col_exp2:
            clean_lyrics = re.sub(r'\[Style:.*?\]\n?', '', result['lyrics'])
            clean_lyrics = re.sub(r'\[Duration:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[BPM:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[Is_MAX_MODE:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[QUALITY:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[REALISM:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[(Male|Female|Duet|Choir|Kids) Vocal\]\s*', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[(Breathy|Powerful|Soft|Clear)\]\s*', '', clean_lyrics)
            
            lyrics_content = f"""CLEAN LYRICS - {result['title']}
{'='*50}

{clean_lyrics.strip()}
"""
            st.download_button(
                "📄 Download Clean Lyrics",
                data=lyrics_content,
                file_name=f"{result['title'].lower().replace(' ', '_')}_lyrics.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col_exp3:
            st.info("""
            **How to Use in Suno:**
            1. Enable *Custom Mode*
            2. Paste Style in "Style of Music"
            3. Paste Lyrics in "Lyrics" field
            4. Click *Create*
            """)

# ============== GENERATE ACTION ==============
if generate_btn:
    if not genre or not topic:
        st.markdown('<div class="error-box">⚠️ <strong>Missing Input:</strong> Please fill in both <em>Genre/Artist</em> and <em>Creative Prompt</em> fields</div>', unsafe_allow_html=True)
    else:
        with st.spinner("🤖 Generating with Groq..."):
            config = {
                "genre": genre,
                "topic": topic,
                "language": language,
                "vocalType": vocal_type,
                "bpm": bpm,
                "duration": duration
            }
            
            result = generate_suno_prompt(config, max_mode, vocal_directing)
            st.session_state.result = result
            st.session_state.last_config = config
            st.rerun()

# ============== FOOTER ==============
st.divider()
st.markdown('<div style="text-align: center; color: #6b7280; font-size: 12px; padding: 20px 0;">🎵 Suno Max Pro v5.0 • Made for Altea</div>', unsafe_allow_html=True)

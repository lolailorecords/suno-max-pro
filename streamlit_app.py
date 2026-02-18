import streamlit as st
import json
import os
import re
from datetime import datetime
from suno_expert import generate_suno_prompt, validate_suno_tags, MAX_MODE_TAGS

# Page config
st.set_page_config(page_title="🎵 Suno Max Pro", page_icon="🎵", layout="wide")

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
    .tag-example {background: rgba(168,85,247,0.1); border: 1px dashed #a855f7; 
                  padding: 0.5rem; border-radius: 0.5rem; font-family: monospace; 
                  font-size: 0.85rem; margin: 0.25rem 0;}
</style>
""", unsafe_allow_html=True)

# Session state
if "result" not in st.session_state:
    st.session_state.result = None
if "last_config" not in st.session_state:
    st.session_state.last_config = {}

# Sidebar
with st.sidebar:
    st.title("⚙️ Config")
    
    # Backend badge
    st.markdown('<div style="background:rgba(59,130,246,0.2);border:1px solid #3b82f6;color:#93c5fd;padding:0.25rem 0.75rem;border-radius:1rem;font-size:0.75rem;font-weight:700">🔵 Backend: Groq Cloud</div>', unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        language = st.text_input("🌐 Language", value="Spanish")
        bpm = st.text_input("🎯 BPM", value="AUTO", help="Enter number or AUTO")
    with col2:
        duration = st.text_input("⏱️ Duration", value="2:30min")
        vocal_type = st.selectbox("🎤 Vocal Type", ["Male", "Female", "Duet", "Choir", "Kids"])
    
    genre = st.text_input("🎸 Genre or Artist", placeholder="e.g., Rosalía, Synthwave, Jazz...", 
                         help="Artist names trigger production-style analysis")
    
    topic = st.text_area("💭 Creative Prompt", placeholder="Describe theme, story, or mood...", height=100)
    
    col_a, col_b = st.columns(2)
    with col_a:
        max_mode = st.toggle("⚡ MAX Mode", value=True, help="Add professional quality tags")
    with col_b:
        vocal_directing = st.toggle("🎙️ Pro Vocals", value=True, 
                                   help="Add detailed vocal direction tags per section")
    
    st.divider()
    
    # 🔧 NEW: Vocal tag examples (when Pro Vocals enabled)
    if vocal_directing:
        with st.expander("🎤 Pro Vocals: Tag Examples"):
            st.markdown("""
            **Section Tags** (added before each section):
            ```
            [Female Vocal] [Breathy] [Reverb] [Verse 1]
            [Male Vocal] [Powerful] [Wide Stereo] [Chorus]
            ```
            
            **Expression Tags** (in parentheses within lyrics):
            ```
            (soft whisper) (building intensity) (powerful belt)
            (spoken) (harmonies enter) (ad-lib: yeah) (falsetto lift)
            ```
            
            **Delivery Variations by Section**:
            • Verses: intimate, storytelling
            • Pre-Chorus: building intensity  
            • Chorus: powerful, memorable hook
            • Bridge: emotional peak or contrast
            """)
    
    generate_btn = st.button("🚀 Generate", type="primary", use_container_width=True)
    
    # Token status
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        st.markdown('<div style="color:#22c55e;font-size:0.75rem">✅ Groq Key: Loaded</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#ef4444;font-size:0.75rem">❌ Groq Key: Missing</div>', unsafe_allow_html=True)

# Main
st.title("🎵 Suno Max Pro")
st.markdown("*Expert AI prompt generator • Quality-optimized • Tag-Validated*")

# 🔧 NEW: Quick tag reference
with st.expander("📚 Suno Tag Reference"):
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("**Structure Tags** (use in lyrics field):")
        for tag in ["Intro", "Verse", "Pre-Chorus", "Chorus", "Bridge", "Outro", "Hook"]:
            st.markdown(f'<div class="tag-example">[{tag}]</div>', unsafe_allow_html=True)
    with col_t2:
        st.markdown("**Vocal Tags** (add before sections):")
        for tag in ["Male Vocal", "Female Vocal", "Breathy", "Powerful", "Reverb", "Wide Stereo"]:
            st.markdown(f'<div class="tag-example">[{tag}]</div>', unsafe_allow_html=True)

# Results
if st.session_state.result:
    result = st.session_state.result
    if result.get("error"):
        st.error(f"❌ {result['error']}")
    else:
        st.markdown(f"""<div class="success-box">
            ✅ Generated with <strong>{result['backend_used'].upper()}</strong>
            • Title: <strong>{result['title']}</strong>
            • Tags validated • Ready for Suno
        </div>""", unsafe_allow_html=True)
        
        col_style, col_lyrics = st.columns(2)
        
        with col_style:
            st.markdown("### 🎛️ Style Prompt")
            st.code(result["style_prompt"], language="text")
            st.caption("💡 Copy to Suno's *Style of Music* field (Custom Mode)")
            
            # 🔧 NEW: Style stats
            style_text = result["style_prompt"]
            char_count = len(style_text)
            tag_count = len([t for t in style_text.split(',') if t.strip() and t.strip().startswith('[')])
            st.markdown(f"<small>📊 {char_count} chars • {tag_count} tags</small>", unsafe_allow_html=True)
            
            # Copy button simulation
            if st.button("📋 Copy Style", key="copy_style"):
                st.toast("Style prompt copied! (Select text + Cmd+C)", icon="✅")
        
        with col_lyrics:
            st.markdown("### 📝 Lyrics & Vocal Tags")
            st.text_area("Lyrics (paste in Suno's *Lyrics* field)", 
                        value=result["lyrics"], 
                        height=400,
                        key="lyrics_display")
            st.caption("💡 Structure tags [Verse], [Chorus] go HERE • Vocal tags BEFORE sections")
            
            # Copy button
            if st.button("📋 Copy Lyrics", key="copy_lyrics"):
                st.toast("Lyrics copied! (Select text + Cmd+C)", icon="✅")
        
        # 🔧 NEW: Preview how it looks in Suno
        with st.expander("👁️ Preview: How This Looks in Suno"):
            st.markdown(f"""
            **Style of Music Field:**
            ```
            {result['style_prompt']}
            ```
            
            **Lyrics Field (Custom Mode):**
            ```
            {result['lyrics'][:500]}...
            ```
            
            **Tips for Best Results:**
            1. Use *Custom Mode* in Suno
            2. Paste Style Prompt in "Style of Music"
            3. Paste Lyrics in "Lyrics" field
            4. Click *Create* → Generate 2 versions, pick best
            5. If vocals aren't right, try adding more [Vocal] tags
            """)
        
        # Export section
        st.divider()
        st.markdown("### 💾 Export")
        
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            prompt_content = f"""🎵 SUNO AI PROMPT - {result['title']}
📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━
🔹 STYLE PROMPT (paste in "Style of Music"):
{result['style_prompt']}

🔹 LYRICS & VOCAL TAGS (paste in "Lyrics" - Custom Mode):
{result['lyrics']}

💡 Pro Tips:
• Use Custom Mode in Suno for best tag support
• MAX_MODE tags work best with Suno Pro subscription
• If vocals aren't right, add more [Vocal Type] tags before sections
• Keep style prompt under 100 chars for best results
"""
            st.download_button(
                "📄 Download Full Prompt .txt",
                data=prompt_content,
                file_name=f"{result['title'].lower().replace(' ', '_')}_suno_prompt.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col_exp2:
            # Clean lyrics version (no tags for reading)
            clean_lyrics = result['lyrics']
            # Remove tag blocks but keep lyrics
            clean_lyrics = re.sub(r'\[Style:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[Duration:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[BPM:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[Is_MAX_MODE:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[QUALITY:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[REALISM:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[REAL_INSTRUMENTS:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[AUDIO_SPEC:.*?\]\n?', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[PRODUCTION:.*?\]\n?', '', clean_lyrics)
            # Keep structure tags but remove vocal tags for clean version
            clean_lyrics = re.sub(r'\[(Male|Female|Duet|Choir|Kids) Vocal\]\s*', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[(Breathy|Powerful|Soft|Clear|Gritty|Smooth|Aggressive|Emotional)\]\s*', '', clean_lyrics)
            clean_lyrics = re.sub(r'\[(Reverb|Delay|AutoTune|Wide Stereo|Centered)\]\s*', '', clean_lyrics)
            
            lyrics_content = f"""📝 CLEAN LYRICS - {result['title']}
Language: {language} | Duration: {duration}
━━━━━━━━━━━━━━━━━━━━━━

{clean_lyrics.strip()}
"""
            st.download_button(
                "📄 Download Clean Lyrics .txt",
                data=lyrics_content,
                file_name=f"{result['title'].lower().replace(' ', '_')}_clean_lyrics.txt",
                mime="text/plain",
                use_container_width=True
            )

# Generate logic
if generate_btn:
    if not genre or not topic:
        st.error("⚠️ Please fill in both *Genre/Artist* and *Creative Prompt* fields")
    else:
        with st.spinner(f"🤖 Generating with GROQ... (Quality mode)"):
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

# Footer
st.divider()
st.markdown('<div style="text-align: center; color: #64748b; font-size: 0.75rem;">🎵 Made for Altea • Quality-Optimized v5.0</div>', unsafe_allow_html=True)

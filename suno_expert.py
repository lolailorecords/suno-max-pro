"""
SUNO EXPERT AI MODULE - Web Search Enhanced v6.0
Real-time artist/song research + Proper Pro Vocals toggle
"""
import os
import json
import re
import requests
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

try:
    from duckduckgo_search import DDGS
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False

load_dotenv()

SUNO_STRUCTURE = ["Intro", "Verse", "Pre-Chorus", "Chorus", "Post-Chorus", "Bridge", "Outro", "Hook"]
SUNO_VOCALS = ["Male Vocal", "Female Vocal", "Duet", "Choir", "Whisper", "Spoken Word", "Rap", "Falsetto", "Belting"]
SUNO_DELIVERY = ["Soft", "Powerful", "Breathy", "Clear", "Gritty", "Smooth", "Aggressive", "Emotional", "Intimate"]
SUNO_EFFECTS = ["Reverb", "Delay", "AutoTune", "Wide Stereo", "Centered", "Harmonies", "3D Harmony", "Ad-libs"]

MAX_MODE_TAGS = """[Is_MAX_MODE: MAX]
[QUALITY: MASTERING_GRADE]
[REALISM: STUDIO_RECORDING]
[REAL_INSTRUMENTS: TRUE]
[AUDIO_SPEC: 24-bit_96kHz_WIDE_STEREO]
[PRODUCTION: PROFESSIONAL_MIX]"""

def validate_suno_tags(text: str) -> str:
    """Clean and validate Suno tags"""
    if not text:
        return text
    # Remove stray characters and AI chatter
    text = re.sub(r'[\{\}\"\\]', '', text)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'\*{2,}', '', text)
    # Remove AI introductory phrases
    text = re.sub(r'Here\'s a.*?prompt.*?:', '', text, flags=re.I)
    text = re.sub(r'Based on research.*?:', '', text, flags=re.I)
    text = re.sub(r'Here is.*?:', '', text, flags=re.I)
    text = re.sub(r'^\s*[-•*]\s*', '', text, flags=re.M)
    # Standardize tags
    for tag in SUNO_STRUCTURE:
        text = re.sub(rf'\[{tag.lower()}\]', f'[{tag}]', text, flags=re.I)
    for tag in SUNO_VOCALS + SUNO_DELIVERY + SUNO_EFFECTS:
        text = re.sub(rf'\[{tag.lower()}\]', f'[{tag}]', text, flags=re.I)
    # Clean up
    text = re.sub(r'\[([^\]]+)\](\s*\[\1\])+', r'[\1]', text)
    text = re.sub(r'\]\[', '] [', text)
    text = re.sub(r'\[\s*\]', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text

def search_web_for_artist(artist_query: str) -> str:
    """Search web for artist/song production style"""
    if not SEARCH_AVAILABLE:
        return "Search unavailable."
    try:
        ddgs = DDGS()
        results_text = []
        queries = [
            f"{artist_query} music production style instrumentation vocal technique",
            f"{artist_query} sound characteristics BPM mixing mastering",
            f"{artist_query} similar artists influences music style"
        ]
        for q in queries:
            results = ddgs.text(q, max_results=2)
            for r in results:
                if 'body' in r:
                    results_text.append(r['body'])
        if not results_text:
            return "No search results found."
        return "\n".join(results_text)[:3000]
    except Exception as e:
        return f"Search error: {str(e)}"

def clean_json_response(text: str) -> Dict[str, Any]:
    """Extract and parse JSON from AI response"""
    if not text:
        return {"success": False, "error": "Empty response"}
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    try:
        return {"success": True, "data": json.loads(text)}
    except:
        pass
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return {"success": True, "data": json.loads(json_match.group())}
        except:
            pass
    result = {}
    title_match = re.search(r'["\']?title["\']?\s*[:=]\s*["\']([^"\']+)["\']', text, re.I)
    if title_match:
        result["title"] = title_match.group(1).strip()
    lyrics_match = re.search(r'["\']?lyrics["\']?\s*[:=]\s*["\']([\s\S]*?)["\']\s*[\},]', text, re.I)
    if lyrics_match:
        result["lyrics"] = lyrics_match.group(1).strip()
    if "lyrics" in result and "title" in result:
        return {"success": True, "data": result}
    return {"success": False, "error": "Could not parse JSON", "raw": text[:200]}

def generate_with_groq(prompt: str, system: str, is_json: bool = False, api_key: str = None) -> Dict[str, Any]:
    """Generate using Groq Cloud API"""
    if not api_key:
        return {"success": False, "error": "Groq API key required", "text": None}
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    model = "llama-3.1-8b-instant"
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    if is_json:
        messages[-1]["content"] += "\n\n⚠️ CRITICAL: ONLY valid JSON. NO extra text. NO markdown. NO introductions."
    payload = {"model": model, "messages": messages, "temperature": 0.1, "max_tokens": 2500, "top_p": 0.9}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        if response.status_code == 429:
            return {"success": False, "error": "Rate limit. Wait 10s.", "text": None}
        if response.status_code == 401:
            return {"success": False, "error": "Invalid Groq API key", "text": None}
        response.raise_for_status()
        result = response.json()
        text = result["choices"][0]["message"]["content"].strip()
        if is_json:
            parsed = clean_json_response(text)
            parsed["text"] = text
            return parsed
        return {"success": True, "data": text, "text": text}
    except Exception as e:
        return {"success": False, "error": f"Groq error: {str(e)}", "text": None}

def generate_suno_prompt(config: Dict[str, str], max_mode: bool = True, vocal_directing: bool = True) -> Dict[str, Any]:
    """Main generation function - with Pro Vocals toggle logic"""
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "GROQ_API_KEY not set in Streamlit Secrets"}
    
    genre = config.get("genre", "").strip()
    topic = config.get("topic", "").strip()
    language = config.get("language", "English")
    vocal_type = config.get("vocalType", "Male")
    bpm = config.get("bpm", "AUTO").strip()
    duration = config.get("duration", "2:30min")
    
    if not genre or not topic:
        return {"error": "Genre and Creative Prompt are required"}
    
    # STEP 1: Web search for artist/song
    search_results = ""
    search_status = "Generic genre (no search)"
    is_artist_like = len(genre.split()) > 1 and any(c.isupper() for c in genre)
    
    if is_artist_like:
        search_results = search_web_for_artist(genre)
        if search_results and "error" not in search_results.lower():
            search_status = f"✅ Web research complete ({len(search_results)} chars)"
        else:
            search_status = "⚠️ Limited search data, using AI knowledge"
    
    # STEP 2: Generate style prompt
    if search_results and "error" not in search_results.lower():
        style_prompt_raw = f"""Analyze this research and create a detailed Suno style prompt (max 1000 chars, comma-separated tags):
RESEARCH: {search_results}
OUTPUT: Only the style tags, no introductions, no explanations."""
        
        style_result = generate_with_groq(style_prompt_raw, 
            "You are a music production expert. Output ONLY style tags, no intro text.", 
            False, api_key)
        style_prompt = style_result.get("data", f"{genre}, contemporary production") if style_result.get("success") else f"{genre}, contemporary production"
        research_used = True
    else:
        style_prompt = f"{genre}, contemporary production, melodic, emotional vocals"
        research_used = False
    
    if bpm.upper() != "AUTO":
        style_prompt = f"{style_prompt}, BPM: {bpm}"
    if max_mode:
        style_prompt = f"{MAX_MODE_TAGS}\n{style_prompt}"
    
    # STEP 3: Generate lyrics (Pro Vocals ON vs OFF)
    if vocal_directing:
        # PRO VOCALS ON - Detailed vocal tags
        lyrics_system = """You are SUNO MASTER. Create lyrics with DETAILED vocal directing:
- BEFORE each section: [Vocal Type] [Delivery] [Effect] [Section]
- WITHIN lyrics: (expression tags) for individual lines
- Use: [Whisper], [Spoken Word], [Harmonies], [3D Harmony], [Falsetto], [Belting], [Ad-libs]
- Vary delivery per section
- 120-250 words for 2-3 min"""
        
        lyrics_prompt = f"""Write song lyrics in {language}.
TOPIC: {topic}
STYLE: {style_prompt}
VOCAL TYPE: {vocal_type}
DURATION: {duration}

OUTPUT JSON ONLY - NO INTRO TEXT:
{{"title": "Song Title", "lyrics": "[Style: {vocal_type} Vocal]\\n[Duration: {duration}]\\n\\n[Intro]\\n(instrumental)\\n\\n[Verse 1]\\n[{vocal_type} Vocal] [Intimate] [Centered]\\nFirst line (whispered)\\nSecond line (building emotion)\\n\\n[Chorus]\\n[{vocal_type} Vocal] [Powerful] [Wide Stereo] [Harmonies]\\nHook line (belt with emotion)\\n\\n[Continue full structure with detailed vocal tags for EVERY section and line]"}}

⚠️ ONLY JSON. NO introductions. NO explanations."""
    else:
        # PRO VOCALS OFF - Basic structure tags only
        lyrics_system = """You are a songwriter. Create lyrics with BASIC structure tags only:
- Use ONLY: [Intro], [Verse], [Pre-Chorus], [Chorus], [Bridge], [Outro]
- NO vocal type tags
- NO delivery tags
- NO expression parentheses
- Clean, simple format"""
        
        lyrics_prompt = f"""Write song lyrics in {language}.
TOPIC: {topic}
STYLE: {style_prompt}
DURATION: {duration}

OUTPUT JSON ONLY - NO INTRO TEXT:
{{"title": "Song Title", "lyrics": "[Style: {vocal_type} Vocal]\\n[Duration: {duration}]\\n\\n[Intro]\\nInstrumental\\n\\n[Verse 1]\\nLyrics here\\n\\n[Chorus]\\nHook lyrics\\n\\n[Continue with basic structure tags only]"}}

⚠️ ONLY JSON. NO vocal tags. NO expression tags. NO introductions."""
    
    lyrics_result = generate_with_groq(lyrics_prompt, lyrics_system, True, api_key)
    
    if not lyrics_result.get("success"):
        return {"error": f"Lyrics generation failed: {lyrics_result.get('error')}"}
    
    content = lyrics_result["data"]
    title = content.get("title", "Untitled").strip() or "Untitled"
    raw_lyrics = content.get("lyrics", "")
    cleaned_lyrics = validate_suno_tags(raw_lyrics)
    
    # Ensure metadata tags at start
    if "[Style:" not in cleaned_lyrics:
        cleaned_lyrics = f"[Style: {vocal_type} Vocal]\n[Duration: {duration}]\n{f'[BPM: {bpm}]' if bpm.upper() != 'AUTO' else ''}\n\n{cleaned_lyrics}"
    
    # Final cleanup - remove any remaining AI chatter
    cleaned_lyrics = re.sub(r'[\{\}\"\\]', '', cleaned_lyrics)
    cleaned_lyrics = re.sub(r'^\s*Here.*?:\s*', '', cleaned_lyrics, flags=re.I | re.M)
    
    return {
        "success": True,
        "style_prompt": validate_suno_tags(style_prompt),
        "title": title,
        "lyrics": cleaned_lyrics,
        "backend_used": "groq",
        "research_used": research_used,
        "search_status": search_status,
        "vocal_directing_used": vocal_directing
    }

"""
SUNO EXPERT AI MODULE - Web Search Enhanced
Real-time artist/song research via DuckDuckGo + Groq Analysis
"""
import os
import json
import re
import requests
import time
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Import search library
try:
    from duckduckgo_search import DDGS
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False

load_dotenv()

# Suno tags
SUNO_STRUCTURE = ["Intro", "Verse", "Pre-Chorus", "Chorus", "Post-Chorus", "Bridge", "Outro", "Hook"]
SUNO_VOCALS = ["Male Vocal", "Female Vocal", "Duet", "Choir", "Whisper", "Rap", "Falsetto", "Belting"]
SUNO_DELIVERY = ["Soft", "Powerful", "Breathy", "Clear", "Gritty", "Smooth", "Aggressive", "Emotional"]

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
    text = re.sub(r'[\{\}\"\\]', '', text)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'\*{2,}', '', text)
    for tag in SUNO_STRUCTURE:
        text = re.sub(rf'\[{tag.lower()}\]', f'[{tag}]', text, flags=re.I)
    for tag in SUNO_VOCALS + SUNO_DELIVERY:
        text = re.sub(rf'\[{tag.lower()}\]', f'[{tag}]', text, flags=re.I)
    text = re.sub(r'\[([^\]]+)\](\s*\[\1\])+', r'[\1]', text)
    text = re.sub(r'\]\[', '] [', text)
    text = re.sub(r'\[\s*\]', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def search_web_for_artist(artist_query: str) -> str:
    """Search web for artist/song production style"""
    if not SEARCH_AVAILABLE:
        return "Search unavailable. Using general knowledge."
    
    try:
        ddgs = DDGS()
        results_text = []
        
        # Query 1: Production style
        q1 = f"{artist_query} music production style instrumentation genre vocal technique"
        results = ddgs.text(q1, max_results=3)
        for r in results:
            if 'body' in r and 'href' in r:
                results_text.append(f"Source: {r['href']}\nInfo: {r['body']}\n")
        
        # Query 2: Specific sonic characteristics
        q2 = f"{artist_query} sound characteristics BPM mixing mastering style"
        results = ddgs.text(q2, max_results=2)
        for r in results:
            if 'body' in r:
                results_text.append(f"Source: {r['href']}\nInfo: {r['body']}\n")
        
        # Query 3: Similar artists and influences
        q3 = f"{artist_query} similar artists influences music style analysis"
        results = ddgs.text(q3, max_results=2)
        for r in results:
            if 'body' in r:
                results_text.append(f"Source: {r['href']}\nInfo: {r['body']}\n")
        
        if not results_text:
            return "No specific search results found. Using general knowledge."
        
        return "\n---\n".join(results_text)
    
    except Exception as e:
        return f"Search error: {str(e)}. Using general knowledge."

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
        messages[-1]["content"] += "\n\n⚠️ CRITICAL: Respond with ONLY valid JSON. No extra text. No markdown."
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
    """Main generation function - with WEB SEARCH research"""
    
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
    
    # STEP 1: WEB SEARCH (if it looks like an artist/song name)
    search_results = ""
    search_status = "No search needed (generic genre)"
    
    # Simple heuristic: if genre has spaces and capital letters, likely artist/song
    if len(genre.split()) > 1 and any(c.isupper() for c in genre):
        search_status = "🔍 Searching web for artist style..."
        search_results = search_web_for_artist(genre)
        search_status = f"✅ Research complete: {len(search_results)} chars of data found"
    
    # STEP 2: Generate style prompt based on research
    if search_results and "Search error" not in search_results and "No specific search" not in search_results:
        style_analysis_prompt = f"""You are a musicologist and Suno AI expert.
        
RESEARCH DATA (from web search):
{search_results}

TASK: Analyze this research and create a DETAILED Suno style prompt (up to 1000 characters).
Include:
1. Exact production style and instrumentation
2. Vocal technique and processing
3. Era, BPM, and mixing characteristics
4. Mood and energy
5. Specific sonic signatures found in research

OUTPUT: A single paragraph of comma-separated tags and descriptions. Be extremely specific based on the research data."""
        
        style_result = generate_with_groq(style_analysis_prompt, 
            "You are a music production expert. Analyze research data and create detailed style prompts.", 
            False, api_key)
        
        if style_result.get("success"):
            style_prompt = style_result["data"].strip()
            research_used = True
        else:
            style_prompt = f"{genre}, contemporary production, melodic, emotional vocals"
            research_used = False
    else:
        # Fallback for generic genres
        style_prompt = f"{genre}, contemporary production, melodic, emotional vocals"
        research_used = False
    
    if bpm.upper() != "AUTO":
        style_prompt = f"{style_prompt}, BPM: {bpm}"
    
    if max_mode:
        style_prompt = f"{MAX_MODE_TAGS}\n{style_prompt}"
    
    # STEP 3: Generate lyrics with vocal directing
    if vocal_directing:
        vocal_directives = """
VOCAL DIRECTING RULES:
1. BEFORE each section: [Type] [Delivery] [Effect]
2. Use (parentheses) for performance directions
3. Vary delivery by section (Verse=intimate, Chorus=powerful)
4. Add expression tags for key lines
5. 120-250 words for 2-3 min song
"""
        lyrics_prompt = f"""Write song lyrics in {language}.
TOPIC: {topic}
RESEARCH-BASED STYLE: {style_prompt}
VOCAL TYPE: {vocal_type}
DURATION: {duration}
RESEARCH USED: {research_used}
{vocal_directives}

OUTPUT FORMAT - JSON ONLY:
{{
  "title": "Catchy Title",
  "lyrics": "[Style: {vocal_type} Vocal, {genre}]\\n[Duration: {duration}]\\n{f'[BPM: {bpm}]' if bpm.upper() != 'AUTO' else ''}\\n\\n[Intro]\\n(instrumental)\\n\\n[Verse 1]\\n[Vocal Tags]\\nLyrics (expression)\\n\\n[Continue full structure...]"
}}

⚠️ CRITICAL: Return ONLY valid JSON. No extra text."""
        
        lyrics_result = generate_with_groq(lyrics_prompt, 
            "You are SUNO MASTER. Create professional prompts with proper vocal tags based on research.", 
            True, api_key)
    else:
        simple_prompt = f"""Write song lyrics in {language}.
Topic: {topic}
Style: {style_prompt}
Include structure tags: [Verse], [Chorus], [Bridge]
Return JSON: {{"title": "...", "lyrics": "..."}}"""
        lyrics_result = generate_with_groq(simple_prompt, "You are a songwriter for Suno AI.", True, api_key)
    
    if not lyrics_result.get("success"):
        return {"error": f"Lyrics generation failed: {lyrics_result.get('error')}"}
    
    content = lyrics_result["data"]
    title = content.get("title", "Untitled").strip() or "Untitled"
    raw_lyrics = content.get("lyrics", "")
    cleaned_lyrics = validate_suno_tags(raw_lyrics)
    
    if "[Style:" not in cleaned_lyrics:
        cleaned_lyrics = f"[Style: {vocal_type} Vocal, {genre}]\n[Duration: {duration}]\n{f'[BPM: {bpm}]' if bpm.upper() != 'AUTO' else ''}\n\n{cleaned_lyrics}"
    
    cleaned_lyrics = re.sub(r'[\{\}\"\\]', '', cleaned_lyrics)
    
    return {
        "success": True,
        "style_prompt": validate_suno_tags(style_prompt),
        "title": title,
        "lyrics": cleaned_lyrics,
        "backend_used": "groq",
        "research_used": research_used,
        "search_status": search_status
    }

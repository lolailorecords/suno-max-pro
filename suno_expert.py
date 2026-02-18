"""
SUNO EXPERT AI MODULE - Groq Backend
Fast, reliable prompt generation for Suno AI
"""
import os
import json
import re
import requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Suno tags reference
SUNO_STRUCTURE_TAGS = ["Intro", "Verse", "Pre-Chorus", "Chorus", "Post-Chorus", "Bridge", "Outro", "Hook"]
SUNO_VOCAL_TAGS = ["Male Vocal", "Female Vocal", "Duet", "Choir", "Whisper", "Rap"]

MAX_MODE_TAGS = """[Is_MAX_MODE: MAX]
[QUALITY: MASTERING_GRADE]
[REALISM: STUDIO_RECORDING]
[REAL_INSTRUMENTS: TRUE]
[AUDIO_SPEC: 24-bit_96kHz_WIDE_STEREO]"""

SUNO_EXPERT_SYSTEM = """You are SUNO MASTER, an expert prompt engineer for Suno AI.
RULES:
1. OUTPUT: Valid JSON only: {"style_prompt": "...", "title": "...", "lyrics": "..."}
2. STYLE: Max 100 chars, comma-separated tags, NO hashtags. Format: "genre, era, instruments, mood"
3. LYRICS: Include [Intro], [Verse], [Chorus], [Bridge], [Outro]. Add vocal tags before sections.
4. ARTIST: If genre is artist name, analyze PRODUCTION STYLE only.
5. LANGUAGE: Lyrics in requested language, tags in English.
6. TITLE: Catchy, max 5 words."""

def validate_suno_tags(text: str) -> str:
    if not text: return text
    # Remove conflicts
    text = re.sub(r'\b(High\s*Energy|Energetic).*\b(Chill|Relaxed)|\b(Chill|Relaxed).*\b(High\s*Energy|Energetic)\b', 'Medium Energy', text, flags=re.I)
    # Standardize tags
    for tag in SUNO_STRUCTURE_TAGS + SUNO_VOCAL_TAGS:
        text = re.sub(rf'\[{tag.lower()}\]', f'[{tag}]', text, flags=re.I)
    # Remove duplicates
    text = re.sub(r'\[([^\]]+)\](\s*\[\1\])+', r'[\1]', text)
    return text.strip()

def generate_with_groq(prompt: str, system: str, is_json: bool = False, api_key: str = None) -> Dict[str, Any]:
    """Generate using Groq Cloud API (fast, reliable, free tier)"""
    if not api_key:
        return {"success": False, "error": "Groq API key required. Add GROQ_API_KEY to Streamlit Secrets.", "text": None}
    
    # Groq API endpoint
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Use Llama 3.1 8B (fast, reliable, good instruction following)
    model = "llama-3.1-8b-instant"
    
    # Format messages for Groq/OpenAI-compatible API
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1024,
    }
    
    # If JSON output requested, add instruction to prompt (Groq doesn't support response_format in free tier)
    if is_json:
        payload["messages"][-1]["content"] += "\n\nIMPORTANT: Respond with valid JSON only, no extra text."
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        text = result["choices"][0]["message"]["content"].strip()
        
        # Clean markdown
        text = re.sub(r'```json\s*|\s*```', '', text)
        
        if is_json:
            try:
                data = json.loads(text)
                return {"success": True, "data": data, "text": text}
            except:
                # Fallback: extract JSON from text
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    try:
                        return {"success": True, "data": json.loads(match.group()), "text": text}
                    except:
                        pass
                return {"success": False, "error": "Could not parse JSON response", "text": text}
        
        return {"success": True, "data": text, "text": text}
        
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out. Try again.", "text": None}
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            return {"success": False, "error": "Rate limit exceeded. Wait 10 seconds and try again.", "text": None}
        elif response.status_code == 401:
            return {"success": False, "error": "Invalid Groq API key. Check your key at console.groq.com", "text": None}
        else:
            return {"success": False, "error": f"Groq API error ({response.status_code}): {str(e)}", "text": None}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}", "text": None}

def generate_suno_prompt(config: Dict[str, str], max_mode: bool = True, vocal_directing: bool = True) -> Dict[str, Any]:
    """Main generation function - Groq backend"""
    
    # Get Groq token
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "GROQ_API_KEY not set in Streamlit Secrets. Add it and redeploy."}
    
    # Prepare prompts
    vocal_instructions = ""
    if vocal_directing:
        vocal_instructions = "Add vocal tags before sections: [Female Vocal] [Soft] before [Verse]"
    
    is_artist = bool(re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', config.get("genre", "")))
    style_task = f"Create Suno style prompt for: {config.get('genre', '')}"
    if is_artist:
        style_task += " (Artist: analyze production style only)"
    if config.get("bpm", "AUTO").upper() != "AUTO":
        style_task += f" Include BPM: {config['bpm']}"
    
    lyrics_task = f"""Write lyrics in {config.get('language', 'English')}.
Topic: {config.get('topic', '')}
Vocal: {config.get('vocalType', 'Male')}
{vocal_instructions}
Include [Style: {config.get('vocalType')} Vocal] at start.
Return JSON: {{"title": "...", "lyrics": "..."}}"""
    
    # Generate with Groq
    style_result = generate_with_groq(style_task, SUNO_EXPERT_SYSTEM, False, api_key)
    lyrics_result = generate_with_groq(lyrics_task, SUNO_EXPERT_SYSTEM, True, api_key)
    
    if not style_result.get("success"):
        return {"error": f"Style failed: {style_result.get('error')}"}
    if not lyrics_result.get("success"):
        return {"error": f"Lyrics failed: {lyrics_result.get('error')}"}
    
    # Process results
    raw_style = validate_suno_tags(style_result["data"])
    content = lyrics_result["data"]
    
    final_style = f"{MAX_MODE_TAGS}\n{raw_style}" if max_mode else raw_style
    bpm_tag = f"[BPM: {config['bpm']}]\n" if config.get("bpm", "AUTO").upper() != "AUTO" else ""
    
    lyrics_content = content.get("lyrics", "") if isinstance(content, dict) else str(content)
    title = content.get("title", "Untitled") if isinstance(content, dict) else "Untitled"
    
    enhanced_lyrics = f"""[Style: {config.get('vocalType')} Vocal, {raw_style}]
[Duration: {config.get('duration', '2:30min')}]
{bpm_tag}
{lyrics_content}"""
    
    return {
        "success": True,
        "style_prompt": validate_suno_tags(final_style),
        "title": title.strip() or "Untitled",
        "lyrics": validate_suno_tags(enhanced_lyrics),
        "backend_used": "groq"
    }

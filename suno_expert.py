"""
SUNO EXPERT AI MODULE - Quality Optimized
Reliable prompt generation with proper tags and vocal directing
"""
import os
import json
import re
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

# 🔧 Comprehensive Suno tag library
SUNO_STRUCTURE = ["Intro", "Verse", "Pre-Chorus", "Chorus", "Post-Chorus", "Bridge", "Outro", "Hook", "Break", "Drop", "Buildup", "Fade Out", "Instrumental", "Solo"]
SUNO_VOCALS = ["Male Vocal", "Female Vocal", "Duet", "Choir", "Whisper", "Spoken Word", "Rap", "Falsetto", "Belting", "Growl", "Harmonies", "Ad-libs", "Background Vocals"]
SUNO_DELIVERY = ["Soft", "Powerful", "Breathy", "Clear", "Gritty", "Smooth", "Aggressive", "Emotional", "Detached", "Intimate"]
SUNO_EFFECTS = ["Reverb", "Delay", "AutoTune", "No AutoTune", "Distortion", "Compression", "Wide Stereo", "Centered", "Panned Left", "Panned Right"]
SUNO_MOOD = ["Uplifting", "Nostalgic", "Dark", "Dreamy", "Energetic", "Chill", "Romantic", "Melancholic", "Joyful", "Angsty", "Confident", "Vulnerable"]
SUNO_PRODUCTION = ["Analog Synths", "Live Drums", "808s", "Acoustic Guitar", "Electric Guitar", "Piano", "Strings", "Brass", "Saxophone", "Bass Guitar", "Tape Saturation", "Lo-fi", "Clean Mix", "Warm Mastering"]

MAX_MODE_TAGS = """[Is_MAX_MODE: MAX]
[QUALITY: MASTERING_GRADE]
[REALISM: STUDIO_RECORDING]
[REAL_INSTRUMENTS: TRUE]
[AUDIO_SPEC: 24-bit_96kHz_WIDE_STEREO]
[PRODUCTION: PROFESSIONAL_MIX]"""

# 🔧 Artist style reference library (for better matching)
ARTIST_STYLE_GUIDE = {
    "rosalía": "flamenco-pop, palmas handclaps, reggaeton beats, auto-tuned vocals, spanish guitar, minimalist production, dramatic dynamics",
    "daft punk": "french house, filtered disco samples, talkbox vocals, analog synths, sidechain compression, robotic effects, funky basslines",
    "the weeknd": "dark r&b, synthwave influences, falsetto vocals, reverb-heavy production, 80s drum machines, atmospheric pads, melancholic mood",
    "taylor swift": "pop-country crossover, storytelling lyrics, acoustic guitar foundation, polished production, catchy hooks, emotional vocal delivery",
    "kendrick lamar": "conscious hip-hop, jazz samples, complex rhyme schemes, dynamic flow switches, layered vocals, social commentary, experimental production",
    "billie eilish": "minimalist pop, whispered vocals, sub-bass drops, ASMR-style production, dark lyrics, intimate recording style, innovative sound design",
    "bad bunny": "latin trap, reggaeton dembow, melodic rap, caribbean percussion, auto-tune melodies, party anthems, spanish lyrics",
    "hans zimmer": "cinematic orchestral, epic brass swells, hybrid electronic-orchestral, powerful percussion, emotional string arrangements, dramatic dynamics"
}

SUNO_EXPERT_SYSTEM = """You are SUNO MASTER v5.0, an expert prompt engineer for Suno AI v4.
CRITICAL OUTPUT RULES:
1. OUTPUT FORMAT: Return ONLY valid JSON with NO extra text, NO markdown, NO code blocks:
   {"style_prompt": "genre, era, instruments, mood, vocal_style", "title": "Song Title", "lyrics": "lyrics with tags"}
2. STYLE PROMPT: MAX 100 characters. Comma-separated tags ONLY. NO hashtags, NO periods, NO quotes.
   Format: "genre_era, instrumentation, mood, vocal_style"
   Example: "80s synthwave, analog synths gated reverb drums, nostalgic, female whisper vocal"
3. LYRICS STRUCTURE: MUST include these tags in lyrics field:
   [Intro], [Verse], [Pre-Chorus], [Chorus], [Bridge], [Outro]
   Capitalize first letter of each tag.
4. VOCAL TAGS: When vocal directing is enabled, add BEFORE each section:
   [Vocal Type] [Delivery] [Effect] before [Section]
   Example: [Female Vocal] [Breathy] [Reverb] [Verse 1]
5. EXPRESSION TAGS: Use (parentheses) for performance directions:
   (soft whisper), (building intensity), (powerful belt), (spoken), (harmonies enter)
6. ARTIST REFERENCES: If user mentions an artist, use PRODUCTION STYLE from reference library.
   Do NOT copy lyrics or themes - only instrumentation, effects, mixing style.
7. LANGUAGE: Write lyrics in requested language. Keep ALL tags in English.
8. TITLE: Create catchy title, max 5 words, Title Case, genre-appropriate.
9. CONFLICT AVOIDANCE: Never combine opposing tags (e.g., [High Energy] + [Chill]).
10. CLEAN OUTPUT: No stray { } [ ] unless they are proper Suno tags. No JSON syntax in lyrics."""

def validate_suno_tags(text: str) -> str:
    """Clean and validate Suno tags - removes stray characters, fixes formatting"""
    if not text:
        return text
    
    # Remove stray JSON/Markdown characters
    text = re.sub(r'[\{\}\"\\]', '', text)  # Remove { } " \
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Remove code blocks
    text = re.sub(r'\*{2,}', '', text)  # Remove bold markdown **
    
    # Remove conflicting energy combinations
    text = re.sub(r'\b(High\s*Energy|Energetic|Upbeat).*\b(Chill|Relaxed|Ambient)|\b(Chill|Relaxed|Ambient).*\b(High\s*Energy|Energetic|Upbeat)\b', 'Medium Energy', text, flags=re.I)
    
    # Standardize structure tags (ensure proper capitalization)
    for tag in SUNO_STRUCTURE:
        text = re.sub(rf'\[{tag.lower()}\]', f'[{tag}]', text, flags=re.I)
        text = re.sub(rf'\[{tag.upper()}\]', f'[{tag}]', text)
    
    # Standardize vocal tags
    for tag in SUNO_VOCALS + SUNO_DELIVERY + SUNO_EFFECTS:
        text = re.sub(rf'\[{tag.lower()}\]', f'[{tag}]', text, flags=re.I)
    
    # Remove duplicate consecutive tags
    text = re.sub(r'\[([^\]]+)\](\s*\[\1\])+', r'[\1]', text)
    
    # Ensure proper spacing around tags
    text = re.sub(r'\]\[', '] [', text)
    
    # Remove empty tags
    text = re.sub(r'\[\s*\]', '', text)
    
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def clean_json_response(text: str) -> Dict[str, Any]:
    """Extract and parse JSON from AI response, with robust fallbacks"""
    if not text:
        return {"success": False, "error": "Empty response"}
    
    # Remove markdown code blocks first
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    
    # Try direct JSON parse
    try:
        return {"success": True, "data": json.loads(text)}
    except:
        pass
    
    # Try to extract JSON object from text
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return {"success": True, "data": json.loads(json_match.group())}
        except:
            pass
    
    # Fallback: try to extract fields manually
    result = {}
    
    # Extract title
    title_match = re.search(r'["\']?title["\']?\s*[:=]\s*["\']([^"\']+)["\']', text, re.I)
    if title_match:
        result["title"] = title_match.group(1).strip()
    
    # Extract style_prompt
    style_match = re.search(r'["\']?style_prompt["\']?\s*[:=]\s*["\']([^"\']+)["\']', text, re.I)
    if style_match:
        result["style_prompt"] = style_match.group(1).strip()
    
    # Extract lyrics (more complex - get everything after "lyrics":)
    lyrics_match = re.search(r'["\']?lyrics["\']?\s*[:=]\s*["\']([\s\S]*?)["\']\s*[\},]', text, re.I)
    if lyrics_match:
        result["lyrics"] = lyrics_match.group(1).strip()
    else:
        # Last resort: assume everything after last "title" or "style_prompt" is lyrics
        parts = re.split(r'["\']?(?:title|style_prompt)["\']?\s*[:=]', text, flags=re.I)
        if len(parts) > 1:
            result["lyrics"] = parts[-1].strip('"\',} ')
    
    if "lyrics" in result and "title" in result:
        return {"success": True, "data": result}
    
    return {"success": False, "error": "Could not parse required fields from response", "raw": text[:200]}

def generate_with_groq(prompt: str, system: str, is_json: bool = False, api_key: str = None) -> Dict[str, Any]:
    """Generate using Groq Cloud API with enhanced error handling"""
    if not api_key:
        return {"success": False, "error": "Groq API key required", "text": None}
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    model = "llama-3.1-8b-instant"
    
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]
    
    # Add JSON instruction for structured output
    if is_json:
        messages[-1]["content"] += "\n\n⚠️ CRITICAL: Respond with ONLY valid JSON. No extra text. No markdown. No explanations."
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.15,  # Lower = more consistent
        "max_tokens": 1500,
        "top_p": 0.9,
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        
        if response.status_code == 429:
            return {"success": False, "error": "Rate limit. Wait 10s and retry.", "text": None}
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

def generate_style_prompt(genre: str, bpm: str, artist_guide: Dict) -> str:
    """Generate style prompt with artist-aware logic"""
    genre_clean = genre.strip().lower()
    
    # Check if it's a known artist
    for artist_key, style_desc in artist_guide.items():
        if artist_key in genre_clean or genre_clean in artist_key:
            # Found artist match - use reference style
            base_style = style_desc
            bpm_part = f", BPM: {bpm}" if bpm.upper() != "AUTO" else ""
            return f"{base_style}{bpm_part}"
    
    # Not a known artist - generate generic but specific style
    # Use simple template for reliability
    style_templates = {
        "pop": "modern pop, polished production, catchy hooks, synth bass, programmed drums",
        "rock": "driving rock, electric guitars, live drums, energetic, powerful vocals",
        "hip hop": "boom bap or trap, 808s, rhythmic flow, urban production, confident delivery",
        "electronic": "electronic dance, synth leads, four-on-floor beat, energetic drops, festival sound",
        "acoustic": "acoustic folk, fingerstyle guitar, warm vocals, intimate recording, organic feel",
        "r&b": "smooth r&b, soulful vocals, laid-back groove, warm bass, emotional delivery",
        "latin": "latin pop or reggaeton, percussion-driven, rhythmic vocals, vibrant production",
        "jazz": "jazz ensemble, upright bass, brushed drums, improvisational, sophisticated harmony",
    }
    
    # Match genre to template
    base_style = "contemporary production, melodic, emotional vocals"  # fallback
    for key, value in style_templates.items():
        if key in genre_clean:
            base_style = value
            break
    
    bpm_part = f", BPM: {bpm}" if bpm.upper() != "AUTO" else ""
    return f"{base_style}{bpm_part}"

def generate_vocal_tags(vocal_type: str, section: str, delivery: str = None, effects: str = None) -> str:
    """Generate proper vocal tags for a section"""
    tags = []
    
    # Vocal type
    if vocal_type:
        tags.append(f"[{vocal_type} Vocal]")
    
    # Delivery style
    if delivery and delivery in SUNO_DELIVERY:
        tags.append(f"[{delivery}]")
    
    # Effects
    if effects:
        for effect in effects.split(","):
            effect = effect.strip()
            if effect in SUNO_EFFECTS:
                tags.append(f"[{effect}]")
    
    # Section tag
    if section:
        # Ensure proper capitalization
        section_cap = section.strip()
        for tag in SUNO_STRUCTURE:
            if tag.lower() in section_cap.lower():
                section_cap = f"[{tag}]"
                break
        else:
            section_cap = f"[{section_cap}]" if not section_cap.startswith("[") else section_cap
        tags.append(section_cap)
    
    return " ".join(tags)

def generate_with_vocal_directing(topic: str, language: str, vocal_type: str, genre: str, 
                                style_prompt: str, duration: str, bpm: str) -> str:
    """Generate lyrics with detailed vocal directing tags"""
    
    # Build detailed vocal instructions
    vocal_directives = """
VOCAL DIRECTING RULES (CRITICAL):
1. BEFORE each section tag, add vocal tags: [Type] [Delivery] [Effect]
   Example: [Female Vocal] [Breathy] [Reverb] [Verse 1]
2. Use (parentheses) for performance directions within lyrics:
   (soft whisper), (building to belt), (spoken), (harmonies enter), (ad-lib: yeah)
3. Vary delivery by section:
   - Verses: intimate, storytelling delivery
   - Pre-Chorus: building intensity
   - Chorus: powerful, memorable hook
   - Bridge: emotional peak or contrast
   - Outro: fading or resolving
4. Add expression tags for key lines:
   (with emotion), (rhythmic rap), (melismatic run), (falsetto lift)
5. Keep lyrics concise: 120-250 words for 2-3 min song
6. Structure: Intro → Verse → Pre-Chorus → Chorus → Verse → Chorus → Bridge → Chorus → Outro
"""
    
    prompt = f"""Write song lyrics in {language}.
TOPIC: {topic}
GENRE STYLE: {style_prompt}
VOCAL TYPE: {vocal_type}
DURATION: {duration}
{vocal_directives}

OUTPUT FORMAT - JSON ONLY:
{{
  "title": "Catchy Title Here",
  "lyrics": "[Style: {vocal_type} Vocal, {genre}]\n[Duration: {duration}]\n{f'[BPM: {bpm}]' if bpm.upper() != 'AUTO' else ''}\n\n[Intro]\n(soft instrumental build)\n\n[Verse 1]\n[Female Vocal] [Intimate] [Centered]\nLyric line here (whispered delivery)\nNext line (building emotion)\n\n[Pre-Chorus]\n[Female Vocal] [Building] [Reverb]\nPre-chorus lyrics (intensity rising)\n\n[Chorus]\n[Female Vocal] [Powerful] [Wide Stereo]\nMemorable hook line (belt with emotion)\nChorus continuation (full voice)\n\n[Continue structure...]\n"
}}

⚠️ CRITICAL: Return ONLY valid JSON. No extra text. No markdown. Proper Suno tags only."""
    
    return prompt

def generate_suno_prompt(config: Dict[str, str], max_mode: bool = True, vocal_directing: bool = True) -> Dict[str, Any]:
    """Main generation function - quality optimized"""
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "GROQ_API_KEY not set in Streamlit Secrets"}
    
    # Extract config with defaults
    genre = config.get("genre", "").strip()
    topic = config.get("topic", "").strip()
    language = config.get("language", "English")
    vocal_type = config.get("vocalType", "Male")
    bpm = config.get("bpm", "AUTO").strip()
    duration = config.get("duration", "2:30min")
    
    if not genre or not topic:
        return {"error": "Genre and Creative Prompt are required"}
    
    # STEP 1: Generate style prompt (artist-aware)
    style_prompt = generate_style_prompt(genre, bpm, ARTIST_STYLE_GUIDE)
    
    # Apply MAX mode if enabled
    if max_mode:
        style_prompt = f"{MAX_MODE_TAGS}\n{style_prompt}"
    
    # STEP 2: Generate lyrics with vocal directing
    if vocal_directing:
        lyrics_prompt = generate_with_vocal_directing(
            topic, language, vocal_type, genre, style_prompt, duration, bpm
        )
        lyrics_result = generate_with_groq(lyrics_prompt, SUNO_EXPERT_SYSTEM, is_json=True, api_key=api_key)
    else:
        # Simple lyrics generation without vocal directing
        simple_prompt = f"""Write song lyrics in {language}.
Topic: {topic}
Style: {style_prompt}
Include basic structure tags: [Verse], [Chorus], [Bridge]
Return JSON: {{"title": "...", "lyrics": "..."}}"""
        lyrics_result = generate_with_groq(simple_prompt, SUNO_EXPERT_SYSTEM, is_json=True, api_key=api_key)
    
    if not lyrics_result.get("success"):
        return {"error": f"Lyrics generation failed: {lyrics_result.get('error')}"}
    
    # Process results
    content = lyrics_result["data"]
    title = content.get("title", "Untitled").strip() or "Untitled"
    raw_lyrics = content.get("lyrics", "")
    
    # Clean and validate lyrics
    cleaned_lyrics = validate_suno_tags(raw_lyrics)
    
    # Ensure required tags are present at start
    if "[Style:" not in cleaned_lyrics:
        cleaned_lyrics = f"[Style: {vocal_type} Vocal, {genre}]\n[Duration: {duration}]\n{f'[BPM: {bpm}]' if bpm.upper() != 'AUTO' else ''}\n\n{cleaned_lyrics}"
    
    # Final validation: remove any remaining stray characters
    cleaned_lyrics = re.sub(r'[\{\}\"\\]', '', cleaned_lyrics)
    
    return {
        "success": True,
        "style_prompt": validate_suno_tags(style_prompt),
        "title": title,
        "lyrics": cleaned_lyrics,
        "backend_used": "groq"
    }

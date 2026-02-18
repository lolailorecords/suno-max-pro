"""
SUNO EXPERT AI MODULE
Handles prompt generation with multiple backend support
"""
import os
import json
import re
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Detect if running on Streamlit Cloud
IS_CLOUD = "STREAMLIT_RUNTIME" in os.environ

# 🔧 Verified Suno tags reference
SUNO_STRUCTURE_TAGS = ["Intro", "Verse", "Pre-Chorus", "Chorus", "Post-Chorus", "Bridge", "Outro", "Hook", "Break", "Drop", "Buildup", "Fade Out", "Instrumental", "Solo"]
SUNO_VOCAL_TAGS = ["Male Vocal", "Female Vocal", "Duet", "Choir", "Whisper", "Spoken Word", "Rap", "Falsetto", "Belting", "Growl", "Harmonies"]
SUNO_MOOD_TAGS = ["Uplifting", "Nostalgic", "Dark", "Dreamy", "Energetic", "Chill", "Romantic", "Aggressive", "Melancholic", "Joyful"]

MAX_MODE_TAGS = """[Is_MAX_MODE: MAX]
[QUALITY: MASTERING_GRADE]
[REALISM: STUDIO_RECORDING]
[REAL_INSTRUMENTS: TRUE]
[AUDIO_SPEC: 24-bit_96kHz_WIDE_STEREO]
[PRODUCTION: PROFESSIONAL_MIX]"""

SUNO_EXPERT_SYSTEM = """You are SUNO MASTER v4.5, an expert prompt engineer for Suno AI v4.
CRITICAL RULES:
1. OUTPUT FORMAT: Always return valid JSON: {"style_prompt": "...", "title": "...", "lyrics": "..."}
2. STYLE PROMPT: MAX 100 chars, comma-separated tags only, NO hashtags, NO periods. Format: "genre, era, instrumentation, mood, vocal_style"
3. LYRICS: ALWAYS include structure tags: [Intro], [Verse], [Chorus], [Bridge], [Outro]. Add vocal tags BEFORE sections.
4. MAX_MODE: Only add quality tags if explicitly requested.
5. ARTIST REFERENCES: Analyze PRODUCTION STYLE → convert to technical tags (not lyrics).
6. BPM: Include only if numeric. Language: Lyrics in requested language, tags in English.
7. TITLE: Catchy, genre-appropriate, max 5 words, Title Case.
8. CONFLICT AVOIDANCE: Never combine opposing tags (e.g., [High Energy] + [Chill]).
9. TAG ORDER: Most important tags first (Suno weights early tags heavier)."""

def validate_suno_tags(text: str) -> str:
    """Clean and validate Suno tags"""
    if not text:
        return text
    
    # Remove conflicting energy combinations
    text = re.sub(r'\b(High\s*Energy|Energetic|Upbeat)\b.*\b(Chill|Relaxed|Ambient)\b|\b(Chill|Relaxed|Ambient)\b.*\b(High\s*Energy|Energetic|Upbeat)\b', 'Medium Energy', text, flags=re.I)
    
    # Standardize structure tags
    for tag in SUNO_STRUCTURE_TAGS:
        text = re.sub(rf'\[{tag.lower()}\]', f'[{tag}]', text, flags=re.I)
    
    # Standardize vocal tags
    for tag in SUNO_VOCAL_TAGS:
        text = re.sub(rf'\[{tag.lower()}\]', f'[{tag}]', text, flags=re.I)
    
    # Remove duplicate consecutive tags
    text = re.sub(r'\[([^\]]+)\](\s*\[\1\])+', r'[\1]', text)
    
    return text.strip()

def generate_with_gemini(prompt: str, system: str, is_json: bool = False, api_key: str = None) -> Dict[str, Any]:
    """Generate using Google Gemini API"""
    import google.generativeai as genai
    
    if not api_key:
        raise ValueError("Gemini API key required")
    
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        system_instruction=system
    )
    
    generation_config = {}
    if is_json:
        generation_config["response_mime_type"] = "application/json"
    
    response = model.generate_content(
        prompt,
        generation_config=generation_config
    )
    
    text = response.text.strip()
    # Clean markdown if present
    text = re.sub(r'```json\s*|\s*```', '', text)
    
    if is_json:
        try:
            return {"success": True, "data": json.loads(text), "text": text}
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON response", "text": text}
    
    return {"success": True, "data": text, "text": text}

def generate_with_ollama(prompt: str, system: str, is_json: bool = False, model: str = None, base_url: str = None) -> Dict[str, Any]:
    """Generate using local Ollama instance (ONLY works on local Mac, NOT on Cloud)"""
    
    # 🔧 FIX: Block Ollama on Streamlit Cloud
    if IS_CLOUD:
        return {"success": False, "error": "Ollama cannot run on Streamlit Cloud. Please use Gemini or Hugging Face backend.", "text": None}
    
    # Lazy import (only import when actually using Ollama)
    try:
        import ollama
    except ImportError:
        return {"success": False, "error": "Ollama package not installed. Run: pip install ollama", "text": None}
    
    model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Format messages for Ollama
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = ollama.chat(
            model=model,
            messages=messages,
            format="json" if is_json else None,
            options={"temperature": 0.3}
        )
        
        text = response["message"]["content"].strip()
        
        if is_json:
            # Clean and parse JSON
            text = re.sub(r'```json\s*|\s*```', '', text)
            try:
                return {"success": True, "data": json.loads(text), "text": text}
            except json.JSONDecodeError:
                return {"success": False, "error": "Invalid JSON from Ollama", "text": text}
        
        return {"success": True, "data": text, "text": text}
        
    except Exception as e:
        return {"success": False, "error": f"Ollama error: {str(e)}", "text": None}

def generate_with_huggingface(prompt: str, system: str, is_json: bool = False, model: str = "meta-llama/Llama-3.2-3B-Instruct", token: str = None) -> Dict[str, Any]:
    """Generate using Hugging Face Inference API"""
    if not token:
        raise ValueError("Hugging Face token required")
    
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Format for HF API
    full_prompt = f"<|system|>\n{system}</s>\n<|user|>\n{prompt}</s>\n<|assistant|>\n"
    
    payload = {
        "inputs": full_prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.3,
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        text = result[0]["generated_text"].strip() if isinstance(result, list) else result["generated_text"].strip()
        text = re.sub(r'```json\s*|\s*```', '', text)
        
        if is_json:
            try:
                return {"success": True, "data": json.loads(text), "text": text}
            except json.JSONDecodeError:
                return {"success": False, "error": "Invalid JSON from HF", "text": text}
        
        return {"success": True, "data": text, "text": text}
        
    except Exception as e:
        return {"success": False, "error": f"HF API error: {str(e)}", "text": None}

def generate_suno_prompt(config: Dict[str, str], max_mode: bool = True, vocal_directing: bool = True) -> Dict[str, Any]:
    """Main function: Generate Suno prompt with selected backend"""
    
    backend = os.getenv("AI_BACKEND", "gemini").lower()
    
    # 🔧 FIX: Force Gemini on Cloud if Ollama is selected
    if IS_CLOUD and backend == "ollama":
        backend = "gemini"
    
    # Prepare prompts
    vocal_instructions = ""
    if vocal_directing:
        vocal_instructions = """PRO VOCAL DIRECTING: Before each section, add technical tags:
• [Vocal Type] [Delivery Style] before [Section]
• Use (parentheses) for ad-libs, harmonies, or effects
• Example: [Female Vocal] [Breathy] [Verse 1] ... (soft whisper: "yeah")"""
    
    # Style prompt generation
    is_artist = bool(re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', config["genre"]))
    style_task = f"Create a Suno style prompt for \"{config['genre']}\"."
    if is_artist:
        style_task += " This is an ARTIST NAME. Analyze their PRODUCTION STYLE: instrumentation, vocal processing, era, mixing techniques. Convert to technical Suno tags."
    else:
        style_task += " This is a GENRE. Focus on characteristic instruments, production style, and mood."
    if config["bpm"].upper() != "AUTO":
        style_task += f" Include BPM: {config['bpm']} at the end."
    
    # Lyrics prompt generation
    lyrics_task = f"""Write song lyrics in {config['language']}.
TOPIC: {config['topic']}
VOCAL TYPE: {config['vocalType']}
{vocal_instructions}
CRITICAL: Include [Style: {config['vocalType']} Vocal, {config['genre']}] at the very start of lyrics.
Return JSON with title and lyrics."""
    
    # Select backend
    if backend == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {"error": "Gemini API key not set. Add GEMINI_API_KEY in Streamlit Secrets."}
        
        style_result = generate_with_gemini(style_task, SUNO_EXPERT_SYSTEM, False, api_key)
        lyrics_result = generate_with_gemini(lyrics_task, SUNO_EXPERT_SYSTEM, True, api_key)
        
    elif backend == "ollama":
        model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        base_url = os.getenv("OLLAMA_BASE_URL")
        
        style_result = generate_with_ollama(style_task, SUNO_EXPERT_SYSTEM, False, model, base_url)
        lyrics_result = generate_with_ollama(lyrics_task, SUNO_EXPERT_SYSTEM, True, model, base_url)
        
    elif backend == "huggingface":
        token = os.getenv("HF_API_TOKEN")
        if not token:
            return {"error": "Hugging Face token not set. Add HF_API_TOKEN in Streamlit Secrets."}
        
        style_result = generate_with_huggingface(style_task, SUNO_EXPERT_SYSTEM, False, token=token)
        lyrics_result = generate_with_huggingface(lyrics_task, SUNO_EXPERT_SYSTEM, True, token=token)
    else:
        return {"error": f"Unknown backend: {backend}"}
    
    # Handle errors
    if not style_result["success"]:
        return {"error": f"Style generation failed: {style_result.get('error')}"}
    if not lyrics_result["success"]:
        return {"error": f"Lyrics generation failed: {lyrics_result.get('error')}"}
    
    # Process results
    raw_style = validate_suno_tags(style_result["data"])
    content = lyrics_result["data"]
    
    # Apply MAX mode
    final_style = f"{MAX_MODE_TAGS}\n{raw_style}" if max_mode else raw_style
    
    # Build lyrics with required tags
    bpm_tag = f"[BPM: {config['bpm']}]\n" if config["bpm"].upper() != "AUTO" else ""
    enhanced_lyrics = f"""[Style: {config['vocalType']} Vocal, {raw_style}]
[Duration: {config['duration']}]
{bpm_tag}
{content['lyrics'] if isinstance(content, dict) else content}"""
    
    return {
        "success": True,
        "style_prompt": validate_suno_tags(final_style),
        "title": content.get("title", "Untitled") if isinstance(content, dict) else "Untitled",
        "lyrics": validate_suno_tags(enhanced_lyrics),
        "backend_used": backend
    }

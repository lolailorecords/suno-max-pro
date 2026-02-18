"""
SUNO EXPERT AI MODULE - Hugging Face Optimized
Reliable prompt generation for Suno AI
"""
import os
import json
import re
import requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

IS_CLOUD = "STREAMLIT_RUNTIME" in os.environ

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

def generate_with_huggingface(prompt: str, system: str, is_json: bool = False, token: str = None) -> Dict[str, Any]:
    """Generate using Hugging Face Inference API (most reliable free option)"""
    if not token:
        return {"success": False, "error": "HF token required. Add HF_API_TOKEN to Secrets.", "text": None}
    
    # Use a reliable, fast model
    model = "meta-llama/Llama-3.2-3B-Instruct"
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Format for Llama 3 chat template
    full_prompt = f"<|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    
    payload = {
        "inputs": full_prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.2,
            "return_full_text": False,
            "do_sample": True
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        
        if response.status_code == 503:
            return {"success": False, "error": "Model is loading. Wait 30s and try again.", "text": None}
        
        response.raise_for_status()
        result = response.json()
        
        # Extract text from response
        if isinstance(result, list) and result:
            text = result[0].get("generated_text", "").strip()
        elif isinstance(result, dict):
            text = result.get("generated_text", "").strip()
        else:
            text = str(result).strip()
        
        # Clean markdown
        text = re.sub(r'```json\s*|\s*```', '', text)
        
        if is_json:
            # Try to parse JSON
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
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"API error: {str(e)}", "text": None}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}", "text": None}

def generate_suno_prompt(config: Dict[str, str], max_mode: bool = True, vocal_directing: bool = True) -> Dict[str, Any]:
    """Main generation function"""
    
    # Use Hugging Face (most reliable)
    token = os.getenv("HF_API_TOKEN")
    if not token:
        return {"error": "HF_API_TOKEN not set in Streamlit Secrets"}
    
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
Return JSON: {{\"title\": \"...\", \"lyrics\": \"...\"}}"""
    
    # Generate
    style_result = generate_with_huggingface(style_task, SUNO_EXPERT_SYSTEM, False, token)
    lyrics_result = generate_with_huggingface(lyrics_task, SUNO_EXPERT_SYSTEM, True, token)
    
    if not style_result.get("success"):
        return {"error": f"Style failed: {style_result.get('error')}"}
    if not lyrics_result.get("success"):
        return {"error": f"Lyrics failed: {lyrics_result.get('error')}"}
    
    # Process
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
        "backend_used": "huggingface"
    }

"""
SUNO EXPERT AI MODULE
Handles prompt generation with multiple backend support
Optimized for Streamlit Cloud + Gemini API
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
    """Generate using Google Gemini API with reliable model fallback"""
    
    if not api_key:
        return {"success": False, "error": "Gemini API key not set. Add GEMINI_API_KEY in Streamlit Secrets.", "text": None}
    
    try:
        import google.generativeai as genai
        from google.api_core.exceptions import InvalidArgument, PermissionDenied, ResourceExhausted, NotFound
    except ImportError:
        return {"success": False, "error": "google-generativeai package not installed. Add to requirements.txt", "text": None}
    
    genai.configure(api_key=api_key)
    
    # 🔧 Most reliable models for free tier (try in order)
    model_names_to_try = [
        "models/gemini-pro",      # ✅ Most reliable for free tier
        "gemini-pro",             # ✅ Alternative format
        "gemini-1.5-flash",       # ✅ If available in your region
    ]
    
    last_error = None
    
    for model_name in model_names_to_try:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system
            )
            
            generation_config = {}
            if is_json:
                generation_config["response_mime_type"] = "application/json"
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                request_options={"timeout": 60}
            )
            
            if not response.text:
                last_error = f"Empty response from {model_name}"
                continue
            
            text = response.text.strip()
            # Clean markdown code blocks if present
            text = re.sub(r'```json\s*|\s*```', '', text)
            
            if is_json:
                try:
                    data = json.loads(text)
                    return {"success": True, "data": data, "text": text, "model_used": model_name}
                except json.JSONDecodeError:
                    # Fallback: try to extract JSON from text
                    json_match = re.search(r'\{.*\}', text, re.DOTALL)
                    if json_match:
                        try:
                            data = json.loads(json_match.group())
                            return {"success": True, "data": data, "text": text, "model_used": model_name}
                        except:
                            pass
                    return {"success": False, "error": "Invalid JSON response from Gemini", "text": text, "model_used": model_name}
            
            return {"success": True, "data": text, "text": text, "model_used": model_name}
            
        except NotFound:
            last_error = f"Model {model_name} not found for your API key"
            continue
        except InvalidArgument as e:
            last_error = f"Invalid request for {model_name}: {str(e)}"
            continue
        except PermissionDenied as e:
            return {"success": False, "error": f"API Key permission denied: {str(e)}. Check your key at aistudio.google.com", "text": None}
        except ResourceExhausted as e:
            return {"success": False, "error": f"Rate limit exceeded: {str(e)}. Wait 60 seconds and try again.", "text": None}
        except Exception as e:
            last_error = f"Error with {model_name}: {type(e).__name__} - {str(e)}"
            continue
    
    # All models failed
    return {"success": False, "error": f"All Gemini models failed. Last error: {last_error}. Try creating a new API key at aistudio.google.com", "text": None}

def generate_with_ollama(prompt: str, system: str, is_json: bool = False, model: str = None, base_url: str = None) -> Dict[str, Any]:
    """Generate using local Ollama instance (ONLY works locally, NOT on Cloud)"""
    
    # 🔧 Block Ollama on Streamlit Cloud
    if IS_CLOUD:
        return {"success": False, "error": "Ollama cannot run on Streamlit Cloud. Please use Gemini or Hugging Face backend.", "text": None}
    
    # Lazy import (only import when actually using Ollama locally)
    try:
        import ollama
    except ImportError:
        return {"success": False, "error": "Ollama package not installed. Run: pip install ollama (local only)", "text": None}
    
    model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = ollama.chat(
            model=model,
            messages=messages,
            format="json" if is_json else None,
            options={"temperature": 0.3, "num_predict": 2048}
        )
        
        text = response["message"]["content"].strip()
        
        if is_json:
            text = re.sub(r'```json\s*|\s*```', '', text)
            try:
                return {"success": True, "data": json.loads(text), "text": text}
            except json.JSONDecodeError:
                return {"success": False, "error": "Invalid JSON from Ollama", "text": text}
        
        return {"success": True, "data": text, "text": text}
        
    except Exception as e:
        return {"success": False, "error": f"Ollama error: {type(e).__name__} - {str(e)}", "text": None}

def generate_with_huggingface(prompt: str, system: str, is_json: bool = False, model: str = "meta-llama/Llama-3.2-3B-Instruct", token: str = None) -> Dict[str, Any]:
    """Generate using Hugging Face Inference API (free tier fallback)"""
    
    if not token:
        return {"success": False, "error": "Hugging Face token not set. Add HF_API_TOKEN in Streamlit Secrets.", "text": None}
    
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Format for HF chat template
    full_prompt = f"<|system|>\n{system}</s>\n<|user|>\n{prompt}</s>\n<|assistant|>\n"
    
    payload = {
        "inputs": full_prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.3,
            "return_full_text": False,
            "do_sample": True
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        
        if response.status_code == 503:
            return {"success": False, "error": "Hugging Face model is loading. Wait 30 seconds and try again.", "text": None}
        
        response.raise_for_status()
        result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            text = result[0].get("generated_text", "").strip()
        elif isinstance(result, dict):
            text = result.get("generated_text", "").strip()
        else:
            text = str(result).strip()
        
        text = re.sub(r'```json\s*|\s*```', '', text)
        
        if is_json:
            try:
                return {"success": True, "data": json.loads(text), "text": text}
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    try:
                        return {"success": True, "data": json.loads(json_match.group()), "text": text}
                    except:
                        pass
                return {"success": False, "error": "Invalid JSON from Hugging Face", "text": text}
        
        return {"success": True, "data": text, "text": text}
        
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"HF API error: {type(e).__name__} - {str(e)}", "text": None}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {type(e).__name__} - {str(e)}", "text": None}

def generate_suno_prompt(config: Dict[str, str], max_mode: bool = True, vocal_directing: bool = True) -> Dict[str, Any]:
    """Main function: Generate Suno prompt with selected backend"""
    
    backend = os.getenv("AI_BACKEND", "gemini").lower()
    
    # 🔧 Force Gemini on Cloud if Ollama is selected
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
    is_artist = bool(re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', config.get("genre", "")))
    style_task = f"Create a Suno style prompt for \"{config.get('genre', '')}\"."
    if is_artist:
        style_task += " This is an ARTIST NAME. Analyze their PRODUCTION STYLE: instrumentation, vocal processing, era, mixing techniques. Convert to technical Suno tags."
    else:
        style_task += " This is a GENRE. Focus on characteristic instruments, production style, and mood."
    if config.get("bpm", "AUTO").upper() != "AUTO":
        style_task += f" Include BPM: {config['bpm']} at the end."
    
    # Lyrics prompt generation
    lyrics_task = f"""Write song lyrics in {config.get('language', 'English')}.
TOPIC: {config.get('topic', '')}
VOCAL TYPE: {config.get('vocalType', 'Male')}
{vocal_instructions}
CRITICAL: Include [Style: {config.get('vocalType', 'Male')} Vocal, {config.get('genre', '')}] at the very start of lyrics.
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
        return {"error": f"Unknown backend: {backend}. Use 'gemini', 'ollama', or 'huggingface'."}
    
    # Handle errors
    if not style_result.get("success"):
        return {"error": f"Style generation failed: {style_result.get('error')}"}
    if not lyrics_result.get("success"):
        return {"error": f"Lyrics generation failed: {lyrics_result.get('error')}"}
    
    # Process results
    raw_style = validate_suno_tags(style_result["data"])
    content = lyrics_result["data"]
    
    # Apply MAX mode
    final_style = f"{MAX_MODE_TAGS}\n{raw_style}" if max_mode else raw_style
    
    # Build lyrics with required tags
    bpm_tag = f"[BPM: {config['bpm']}]\n" if config.get("bpm", "AUTO").upper() != "AUTO" else ""
    
    if isinstance(content, dict):
        lyrics_content = content.get("lyrics", "")
        title = content.get("title", "Untitled")
    else:
        lyrics_content = str(content)
        title = "Untitled"
    
    enhanced_lyrics = f"""[Style: {config.get('vocalType', 'Male')} Vocal, {raw_style}]
[Duration: {config.get('duration', '2:30min')}]
{bpm_tag}
{lyrics_content}"""
    
    return {
        "success": True,
        "style_prompt": validate_suno_tags(final_style),
        "title": title.strip() if title else "Untitled",
        "lyrics": validate_suno_tags(enhanced_lyrics),
        "backend_used": backend
    }

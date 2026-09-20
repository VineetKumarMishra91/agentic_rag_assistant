import json
import re
from google import genai
from backend import config

def transcribe_and_summarize_media(file_path: str) -> dict:
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    uploaded_file = client.files.upload(file=file_path)
    
    prompt = """
    Analyze the following media file.
    Return a JSON object with EXACTLY these three keys:
    - "transcript": The full text transcript of the audio/video.
    - "summary": A brief summary of the contents.
    - "action_items": A list of strings representing action items.
    Respond ONLY with valid JSON.
    """
    
    response = client.models.generate_content(
        model=config.GEMINI_CHAT_MODEL,
        contents=[uploaded_file, prompt]
    )
    
    text = response.text
    text = re.sub(r'```(?:json)?\n?(.*?)\n?```', r'\1', text, flags=re.DOTALL).strip()
    
    try:
        return json.loads(text)
    except Exception:
        return {"transcript": text, "summary": "Failed to parse JSON", "action_items": []}

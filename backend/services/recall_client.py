import json
import re
import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from backend import config
from backend.services.rag_pipeline import ingest_media_transcript
from backend.services.mongo_client import save_media_metadata

def handle_recall_webhook(payload: dict) -> dict:
    if payload.get("event") != "transcript.done":
        return {"status": "ignored"}
        
    data = payload.get("data", {})
    bot_id = data.get("bot_id", "unknown_bot")
    meeting_id = data.get("meeting_id", "unknown_meeting")
    transcript_obj = data.get("transcript", {})
    transcript_text = transcript_obj.get("text", "")
    
    source_id = f"recall_{meeting_id}"
    source_name = f"Meeting {meeting_id}"
    
    prompt = PromptTemplate.from_template(
        "Analyze the following meeting transcript.\n"
        "Return a JSON object with EXACTLY two keys:\n"
        "- \"summary\": A brief summary of the meeting.\n"
        "- \"action_items\": A list of action items from the meeting.\n"
        "Respond ONLY with valid JSON.\n\n"
        "Transcript:\n{transcript}"
    )
    llm = ChatGoogleGenerativeAI(model=config.GEMINI_CHAT_MODEL, google_api_key=config.GEMINI_API_KEY)
    chain = prompt | llm
    response = chain.invoke({"transcript": transcript_text})
    
    text = response.content
    if isinstance(text, list):
        text = "".join([b.get("text", "") for b in text if isinstance(b, dict) and "text" in b])
        
    text = re.sub(r'```(?:json)?\n?(.*?)\n?```', r'\1', text, flags=re.DOTALL).strip()
    
    try:
        parsed = json.loads(text)
    except Exception:
        parsed = {"summary": "Failed to parse summary", "action_items": []}
        
    ingest_media_transcript(transcript_text, source_id, "meeting", source_name)
    save_media_metadata(
        source_id=source_id,
        source_name=source_name,
        source_type="meeting",
        transcript=transcript_text,
        summary=parsed.get("summary", ""),
        action_items=parsed.get("action_items", []),
        upload_date=datetime.datetime.utcnow()
    )
    
    return {
        "source_id": source_id,
        "summary": parsed.get("summary", ""),
        "action_items": parsed.get("action_items", []),
        "status": "ingested"
    }

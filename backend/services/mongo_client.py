import datetime
from pymongo import MongoClient
from backend.config import MONGODB_URI

client = None

def get_mongo_db():
    global client
    if client is None:
        # Default to localhost if MONGODB_URI is not set
        uri = MONGODB_URI or "mongodb://localhost:27017"
        client = MongoClient(uri)
    return client.get_database("agentic_rag")

def save_document_metadata(source_id: str, filename: str, upload_date: datetime.datetime, status: str):
    db = get_mongo_db()
    collection = db["documents"]
    
    doc = {
        "source_id": source_id,
        "filename": filename,
        "upload_date": upload_date,
        "status": status
    }
    
    collection.insert_one(doc)

def save_media_metadata(source_id: str, source_name: str, source_type: str, transcript: str, summary: str, action_items: list, upload_date: datetime.datetime):
    db = get_mongo_db()
    collection = db["media"]
    
    doc = {
        "source_id": source_id,
        "source_name": source_name,
        "source_type": source_type,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "upload_date": upload_date
    }
    
    collection.insert_one(doc)

def log_tool_call(tool_name: str, tool_input: dict, tool_output: str, timestamp: datetime.datetime):
    db = get_mongo_db()
    collection = db["tool_call_log"]
    
    doc = {
        "tool_name": tool_name,
        "input": tool_input,
        "output": tool_output,
        "timestamp": timestamp
    }
    
    collection.insert_one(doc)

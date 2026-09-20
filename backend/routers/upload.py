import os
import uuid
import datetime
import tempfile
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.services.rag_pipeline import ingest_document
from backend.services.mongo_client import save_document_metadata

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    source_id = str(uuid.uuid4())
    upload_date = datetime.datetime.utcnow()
    
    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, f"{source_id}_{file.filename}")
    
    with open(tmp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        chunks_created = ingest_document(tmp_path, source_id, file.filename)
        save_document_metadata(source_id, file.filename, upload_date, "ingested")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            
    return {
        "source_id": source_id,
        "status": "ingested",
        "chunks_created": chunks_created
    }

@router.post("/upload/video")
async def upload_video(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    source_id = str(uuid.uuid4())
    upload_date = datetime.datetime.utcnow()
    
    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, f"{source_id}_{file.filename}")
    
    with open(tmp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        from backend.services.gemini_client import transcribe_and_summarize_media
        result = transcribe_and_summarize_media(tmp_path)
        
        transcript = result.get("transcript", "")
        summary = result.get("summary", "")
        action_items = result.get("action_items", [])
        
        from backend.services.rag_pipeline import ingest_media_transcript
        from backend.services.mongo_client import save_media_metadata
        
        ingest_media_transcript(transcript, source_id, "video", file.filename)
        
        save_media_metadata(
            source_id=source_id,
            source_name=file.filename,
            source_type="video",
            transcript=transcript,
            summary=summary,
            action_items=action_items,
            upload_date=upload_date
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            
    return {
        "source_id": source_id,
        "summary": summary,
        "action_items": action_items,
        "status": "ingested"
    }

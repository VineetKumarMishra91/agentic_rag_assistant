from fastapi import APIRouter, HTTPException
from backend.services.mongo_client import get_mongo_db

router = APIRouter()

@router.get("/sources")
def list_sources():
    try:
        db = get_mongo_db()
        docs = list(db["documents"].find({}, {"_id": 0}))
        media = list(db["media"].find({}, {"_id": 0}))
        
        sources = []
        for d in docs:
            sources.append({
                "source_id": d.get("source_id"),
                "name": d.get("filename", "Unknown Document"),
                "source_type": "document",
                "upload_date": d.get("upload_date")
            })
            
        for m in media:
            sources.append({
                "source_id": m.get("source_id"),
                "name": m.get("source_name", "Unknown Media"),
                "source_type": m.get("source_type", "media"),
                "upload_date": m.get("upload_date")
            })
            
        # Sort by upload_date descending. If upload_date is missing, put it at the end.
        sources.sort(key=lambda x: x["upload_date"] if x["upload_date"] else "", reverse=True)
        return {"sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

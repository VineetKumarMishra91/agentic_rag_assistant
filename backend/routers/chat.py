from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.rag_pipeline import answer_from_source
from backend.services.web_search import web_search_answer

router = APIRouter()

class ChatQuery(BaseModel):
    query: str

@router.post("/documents/{source_id}/chat")
async def document_chat(source_id: str, request: ChatQuery):
    try:
        return answer_from_source(request.query, source_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/{source_id}/chat/web-search")
async def document_chat_web_search(source_id: str, request: ChatQuery):
    try:
        return web_search_answer(request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.agent import run_agent

router = APIRouter()

class AgentQuery(BaseModel):
    query: str

@router.post("/assistant/chat")
async def assistant_chat(request: AgentQuery):
    try:
        return run_agent(request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

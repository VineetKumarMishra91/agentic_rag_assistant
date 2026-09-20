from fastapi import APIRouter, HTTPException
from backend.models.webhook import RecallWebhookPayload
from backend.services.recall_client import handle_recall_webhook

router = APIRouter()

@router.post("/meetings/webhook")
async def meetings_webhook(payload: RecallWebhookPayload):
    try:
        return handle_recall_webhook(payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel

class TranscriptData(BaseModel):
    text: str

class RecallWebhookData(BaseModel):
    bot_id: str
    meeting_id: str
    transcript: TranscriptData

class RecallWebhookPayload(BaseModel):
    event: str
    data: RecallWebhookData

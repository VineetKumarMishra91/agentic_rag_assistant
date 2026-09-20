from fastapi import FastAPI
from backend.routers import upload, chat, meetings, agent, sources

app = FastAPI()

app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(meetings.router)
app.include_router(agent.router)
app.include_router(sources.router)

@app.get("/health")
def health():
    return {"status": "ok"}

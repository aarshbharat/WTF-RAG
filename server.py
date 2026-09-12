"""
Web server for the JS frontend: serves web/ and exposes a small JSON API.

    uv run uvicorn server:app --reload --port 8000
"""
import json

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import PLAYLIST_FILE
from rag import WTFRag, fmt_time
import mimetypes

mimetypes.add_type("image/svg+xml", ".svg")     # Windows' registry often gets these wrong
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")

app = FastAPI(title="Cue - ask the WTF archive")
rag = None                                   # loaded once on startup, reused for every request


class Question(BaseModel):
    question: str


@app.on_event("startup")
def startup():
    global rag
    rag = WTFRag()


@app.on_event("shutdown")
def shutdown():
    if rag:
        rag.close()


@app.get("/api/episodes")
def episodes():
    with open(PLAYLIST_FILE, encoding="utf-8") as f:
        eps = json.load(f)
    return [{"video_id": e["video_id"], "title": e["title"], "minutes": round((e["duration"] or 0) / 60)}
            for e in eps]


@app.post("/api/ask")
def ask(payload: Question):
    question = payload.question.strip()
    if not question:
        raise HTTPException(400, "Ask a question first.")
    if len(question) > 500:
        raise HTTPException(400, "Keep the question under 500 characters.")
    try:
        result = rag.ask(question)
    except Exception as e:
        raise HTTPException(503, f"The answer service is unavailable right now ({type(e).__name__}).")
    return {
        "answer": result["answer"],
        "sources": [{"n": i, "video_id": s["video_id"], "title": s["title"],
                     "start": s["link_start"], "timecode": fmt_time(s["link_start"]),
                     "url": s["url"], "text": s["text"]}
                    for i, s in enumerate(result["sources"], 1)],
    }


app.mount("/", StaticFiles(directory="web", html=True), name="web")
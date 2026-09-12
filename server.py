"""
Web server: serves web/ and exposes the JSON API used by the frontend.

Local:  uv run uvicorn server:app --reload --port 8000
Docker: uvicorn server:app --host 0.0.0.0 --port $PORT --workers 1
"""
import json
import mimetypes
import os
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import PLAYLIST_FILE
from rag import WTFRag, fmt_time

# Windows reads these from the registry and often gets them wrong, which stops
# the favicon and even the JS from loading. Setting them explicitly is harmless on Linux.
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")

MAX_PER_HOUR = int(os.getenv("MAX_QUESTIONS_PER_HOUR", "15"))

app = FastAPI(title="WTF Rewind")
rag = None                                   # loaded once on startup, reused per request
_asks = defaultdict(deque)                   # caller ip -> times of recent questions


class Question(BaseModel):
    question: str


def check_rate_limit(request: Request):
    """A public app spends your Groq quota. Cap what one visitor can use."""
    now = time.time()
    seen = _asks[request.client.host if request.client else "unknown"]
    while seen and now - seen[0] > 3600:
        seen.popleft()
    if len(seen) >= MAX_PER_HOUR:
        raise HTTPException(429, "That's a lot of questions in one hour. Try again later.")
    seen.append(now)


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
    return [{"video_id": e["video_id"], "title": e["title"],
             "minutes": round((e["duration"] or 0) / 60)} for e in eps]


@app.post("/api/ask")
def ask(payload: Question, request: Request):
    check_rate_limit(request)
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
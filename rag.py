"""
Step B: the RAG core. Question in -> answer + timestamped sources out.

    uv run rag.py what are the biggest challenges in running a restaurant
"""
import json
import sys

from dotenv import load_dotenv

from config import (TRANSCRIPTS_DIR, QDRANT_PATH, COLLECTION, EMBED_MODEL,
                    GROQ_MODEL, TOP_K, CONTEXT_PAD_SEC)
from make_windows import clean

SYSTEM_PROMPT = """You help entrepreneurs by answering questions using ONLY the podcast \
excerpts provided, which come from "WTF is with Nikhil Kamath".

Rules:
- Use only the excerpts. If they don't contain the answer, say clearly that the \
podcast excerpts don't cover it. Do not fill gaps with outside knowledge.
- Cite every claim with the excerpt number in square brackets, like [1] or [2][4].
- The excerpts are auto-generated captions with no speaker labels and some \
transcription errors. Don't name who said something unless the excerpt itself makes it clear.
- Start with a short direct answer, then the key points. Keep it concise."""


def fmt_time(seconds):
    s = int(seconds)
    h, m, s = s // 3600, (s % 3600) // 60, s % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def build_sources(hits, segments_by_video, pad=CONTEXT_PAD_SEC):
    """Turn search hits into context passages.

    Each hit is widened by `pad` seconds on both sides (small-to-big), hits whose
    widened ranges overlap in the same episode are merged, and the passage text is
    rebuilt from the original transcript segments, so overlapping windows never
    duplicate text.
    """
    spans = sorted(
        ((h.payload["video_id"], max(0.0, h.payload["start"] - pad), h.payload["end"] + pad, h)
         for h in hits),
        key=lambda s: (s[0], s[1]),
    )
    merged = []
    for vid, start, end, hit in spans:
        if merged and merged[-1]["video_id"] == vid and start <= merged[-1]["end"]:
            merged[-1]["end"] = max(merged[-1]["end"], end)
            merged[-1]["hits"].append(hit)
        else:
            merged.append({"video_id": vid, "title": hit.payload["title"],
                           "start": start, "end": end, "hits": [hit]})

    for src in merged:
        segs = segments_by_video[src["video_id"]]
        src["text"] = " ".join(t for t in (clean(s["text"]) for s in segs
                                           if src["start"] <= s["start"] < src["end"]) if t)
        best = max(src["hits"], key=lambda h: h.score)
        src["score"] = best.score
        src["link_start"] = int(best.payload["start"])       # jump to the best-matching window
        src["url"] = f"https://youtu.be/{src['video_id']}?t={src['link_start']}"
        del src["hits"]

    merged.sort(key=lambda s: -s["score"])                   # best source becomes [1]
    return merged


def build_user_message(question, sources):
    parts = [f"[{i}] Episode: {s['title']} (at {fmt_time(s['link_start'])})\n{s['text']}"
             for i, s in enumerate(sources, 1)]
    return "Podcast excerpts:\n\n" + "\n\n".join(parts) + f"\n\nQuestion: {question}"


class WTFRag:
    """Loads everything once; Streamlit will cache a single instance of this."""

    def __init__(self):
        from groq import Groq
        from qdrant_client import QdrantClient
        from sentence_transformers import SentenceTransformer

        load_dotenv()
        self.embedder = SentenceTransformer(EMBED_MODEL)
        self.db = QdrantClient(path=str(QDRANT_PATH))
        self.llm = Groq()                                    # reads GROQ_API_KEY from .env
        self.segments = {}
        for p in TRANSCRIPTS_DIR.glob("*.json"):
            with open(p, encoding="utf-8") as f:
                ep = json.load(f)
            self.segments[ep["video_id"]] = ep["segments"]

    def retrieve(self, question, k=TOP_K):
        q = self.embedder.encode("query: " + question, normalize_embeddings=True)
        return self.db.query_points(COLLECTION, query=q.tolist(), limit=k).points

    def ask(self, question, k=TOP_K):
        sources = build_sources(self.retrieve(question, k), self.segments)
        response = self.llm.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": build_user_message(question, sources)}],
            temperature=0.2,
            max_tokens=1500,
            reasoning_effort="low",
        )
        return {"answer": response.choices[0].message.content, "sources": sources,
                "usage": response.usage}

    def close(self):
        self.db.close()


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "how do restaurants make money"
    rag = WTFRag()
    try:
        result = rag.ask(question)
        print(result["answer"], "\n")
        for i, s in enumerate(result["sources"], 1):
            print(f"[{i}] {s['score']:.3f}  {s['title'][:45]}  {s['url']}")
        print(f"\ntokens: {result['usage'].prompt_tokens} in, {result['usage'].completion_tokens} out")
    finally:
        rag.close()
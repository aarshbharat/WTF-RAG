from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLVPkbpccdn98Mb43hFbfxXHRLQxAS4tyU"
PLAYLIST_FILE = DATA / "playlist.json"
TRANSCRIPTS_DIR = DATA / "transcripts"
WINDOWS_FILE = DATA / "windows.jsonl"
MIN_WORDS = 30   # windows below this are outros/pleasantries (see inspect_windows.py)

CAPTION_LANGS = ["en-IN", "en"]   # human en-IN first, then en (human, else auto) # English first, Hindi as fallback
WINDOW_SEC = 60
OVERLAP_SEC = 15
# Episodes whose human caption track is incomplete (found by check_transcripts.py)
CAPTION_OVERRIDES = {
    "FPV5fAkqyBs": ["en"],   # human en-IN: 11 words/min, ends at 237/255 min
    "2_yA6GoqUnY": ["en"],   # human en-IN: 21 words/min, sparse despite full coverage
}

EMBED_MODEL = "intfloat/multilingual-e5-small"
EMBEDDINGS_FILE = DATA / "embeddings.npy"
IDS_FILE = DATA / "embedding_ids.json"

def embeddings_file(variant):
    return DATA / f"embeddings_{variant}.npy"     # e.g. embeddings_title.npy

EMBED_VARIANT = "notitle"
QDRANT_PATH = DATA / "qdrant"
COLLECTION = "wtf_windows"

GROQ_MODEL = "openai/gpt-oss-120b"
TOP_K = 6
CONTEXT_PAD_SEC = 45

"""
Step 2: download the caption transcript for every episode in data/playlist.json.

Prefers human-made English captions (en-IN, then en) and falls back to
YouTube's auto-generated English. Saves one JSON per episode:
data/transcripts/<video_id>.json
"""
import json
import time

from youtube_transcript_api import YouTubeTranscriptApi

from config import PLAYLIST_FILE, TRANSCRIPTS_DIR, CAPTION_LANGS, CAPTION_OVERRIDES

        
            

TRANSCRIPTS_DIR.mkdir(exist_ok=True)
ytt = YouTubeTranscriptApi()

with open(PLAYLIST_FILE, encoding="utf-8") as f:
    episodes = json.load(f)

for i, ep in enumerate(episodes, 1):
    vid = ep["video_id"]
    tag = f"[{i}/{len(episodes)}] {vid}"
    out = TRANSCRIPTS_DIR / f"{vid}.json"

    if out.exists():                      # safe to re-run: skip finished episodes
        print(f"{tag}: already saved, skipping")
        continue
    langs = CAPTION_OVERRIDES.get(vid, CAPTION_LANGS)

    try:
        fetched = ytt.fetch(vid, languages=langs)
    except Exception as e:
        print(f"{tag}: FAILED ({type(e).__name__}) - re-run later to retry")
        continue

    segments = [s for s in fetched.to_raw_data() if s["text"].strip()]
    data = {
        "video_id": vid,
        "title": ep["title"],
        "duration": ep["duration"],
        "caption_lang": fetched.language_code,
        "caption_auto": fetched.is_generated,
        "segments": segments,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    kind = "auto" if fetched.is_generated else "human"
    print(f"{tag}: {len(segments)} segments ({fetched.language_code}, {kind})")
    time.sleep(2)                         # be polite to YouTube
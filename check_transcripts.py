import json
from config import TRANSCRIPTS_DIR

for p in sorted(TRANSCRIPTS_DIR.glob("*.json")):
    d = json.load(open(p, encoding="utf-8"))
    segs = d["segments"]
    dur_min = (d["duration"] or 0) / 60
    last_min = segs[-1]["start"] / 60
    words = sum(len(s["text"].split()) for s in segs)
    wpm = words / dur_min if dur_min else 0
    kind = "auto" if d["caption_auto"] else "human"
    print(f"{d['video_id']}  {kind:5}  {len(segs):5} segs  covers {last_min:4.0f}/{dur_min:4.0f} min  {wpm:4.0f} words/min")
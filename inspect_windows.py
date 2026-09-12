import json
from config import WINDOWS_FILE

rows = [json.loads(line) for line in open(WINDOWS_FILE, encoding="utf-8")]
last_window = {r["video_id"]: r["window_id"] for r in rows}   # last one per episode wins

for r in rows:
    n = len(r["text"].split())
    if n < 30 or n > 280:
        tag = "LAST" if r["window_id"] == last_window[r["video_id"]] else ""
        span = r["end"] - r["start"]
        print(f"{r['window_id']}  {n:3d} words  {span:5.1f}s  {tag:4}  "
              f"auto={r['caption_auto']!s:5}  {r['text'][:60]}")
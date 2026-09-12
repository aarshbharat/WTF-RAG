import json, time
from youtube_transcript_api import YouTubeTranscriptApi
from config import PLAYLIST_FILE

ytt = YouTubeTranscriptApi()
episodes = json.load(open(PLAYLIST_FILE, encoding="utf-8"))

for ep in episodes:
    try:
        langs = [t.language_code + (" (auto)" if t.is_generated else "") for t in ytt.list(ep["video_id"])]
    except Exception as e:
        langs = [f"NONE ({type(e).__name__})"]
    mins = (ep["duration"] or 0) // 60
    print(f"{ep['video_id']}  {mins:>4} min  {', '.join(langs):<25} {(ep['title'] or '')[:45]}")
    time.sleep(1)   # be polite to YouTube
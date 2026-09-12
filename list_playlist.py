import json
from yt_dlp import YoutubeDL
from config import PLAYLIST_URL, PLAYLIST_FILE

with YoutubeDL({"extract_flat": "in_playlist", "quiet": True}) as ydl:
    info = ydl.extract_info(PLAYLIST_URL, download=False)

episodes = [{"video_id": e["id"], "title": e.get("title"), "duration": e.get("duration")}
            for e in info["entries"]]

with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
    json.dump(episodes, f, ensure_ascii=False, indent=2)

total_hours = sum(e["duration"] or 0 for e in episodes) / 3600
print(f"{len(episodes)} episodes, about {total_hours:.0f} hours total")
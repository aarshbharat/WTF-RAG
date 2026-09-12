"""
Step 3: cut every transcript into overlapping time windows.

Input : data/transcripts/<video_id>.json   (one file per episode)
Output: data/windows.jsonl                 (one window per line, all episodes)
"""
import json
import re

from config import TRANSCRIPTS_DIR, WINDOWS_FILE, WINDOW_SEC, OVERLAP_SEC, MIN_WORDS

NOISE = re.compile(r"\[[^\]]*\]")                    # [Music], [Applause], [Laughter] ...
EP_PREFIX = re.compile(r"^\s*(WTF\s+)?(Ep\.?\s*)?#?\s*\d+\s*[|:.]?\s*", re.IGNORECASE)


def clean(text):
    text = NOISE.sub(" ", text).replace(">>", " ")     # drop tags and speaker-change arrows
    return re.sub(r"\s+", " ", text).strip()


def short_title(title):
    """'Ep #3| WTF is E-commerce: ...' -> 'WTF is E-commerce: ...'"""
    return EP_PREFIX.sub("", title or "").strip()


def make_windows(segments, window_sec=WINDOW_SEC, overlap_sec=OVERLAP_SEC):
    segs = [{"start": s["start"], "duration": s["duration"], "text": clean(s["text"])}
            for s in segments]
    segs = [s for s in segs if s["text"]]

    windows, i = [], 0
    while i < len(segs):
        start = segs[i]["start"]
        j = i
        while j < len(segs) and segs[j]["start"] < start + window_sec:
            j += 1
        end = segs[j]["start"] if j < len(segs) else segs[-1]["start"] + segs[-1]["duration"]
        windows.append({"start": round(start, 1), "end": round(end, 1),
                        "text": " ".join(s["text"] for s in segs[i:j])})
        if j >= len(segs):
            break
        next_start = start + window_sec - overlap_sec
        k = i + 1
        while k < len(segs) and segs[k]["start"] < next_start:
            k += 1
        i = k
    return windows


if __name__ == "__main__":
    files = sorted(TRANSCRIPTS_DIR.glob("*.json"))
    total, word_counts = 0, []
    dropped = 0

    with open(WINDOWS_FILE, "w", encoding="utf-8") as out:
        for p in files:
            with open(p, encoding="utf-8") as f:
                ep = json.load(f)
                windows = make_windows(ep["segments"])
                kept = 0
                for n, w in enumerate(windows):          # n counts ALL windows, so IDs stay stable
                    n_words = len(w["text"].split())
                    if n_words < MIN_WORDS:
                        dropped += 1
                        continue
                    record = {
                        "window_id": f"{ep['video_id']}_{n:04d}",
                        "video_id": ep["video_id"],
                        "title": short_title(ep["title"]),
                        "caption_auto": ep["caption_auto"],
                        **w,
                    }
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    word_counts.append(n_words)
                    kept += 1
                total += kept
                print(f"{ep['video_id']}  {kept:4d} windows  {short_title(ep['title'])[:50]}")

    word_counts.sort()
    print(f"\n{len(files)} episodes -> {total} windows written to {WINDOWS_FILE.name}")
    print(f"words per window: median {word_counts[len(word_counts)//2]}, "
          f"min {word_counts[0]}, max {word_counts[-1]}")
    print(f"\n{len(files)} episodes -> {total} windows written ({dropped} dropped under {MIN_WORDS} words)")
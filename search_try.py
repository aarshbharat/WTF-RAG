import json, sys
import numpy as np
from sentence_transformers import SentenceTransformer
from config import WINDOWS_FILE, EMBED_MODEL, EMBEDDINGS_FILE, IDS_FILE

rows = [json.loads(line) for line in open(WINDOWS_FILE, encoding="utf-8")]
assert json.load(open(IDS_FILE)) == [r["window_id"] for r in rows], \
    "windows.jsonl changed since embedding - re-run embed.py"
vecs = np.load(EMBEDDINGS_FILE)
model = SentenceTransformer(EMBED_MODEL)

query = " ".join(sys.argv[1:]) or "how do restaurants make money"
q = model.encode("query: " + query, normalize_embeddings=True)
scores = vecs @ q
for i in scores.argsort()[::-1][:5]:
    r = rows[i]
    print(f"{scores[i]:.3f}  {r['title'][:40]}  https://youtu.be/{r['video_id']}?t={int(r['start'])}")
    print(f"       {r['text'][:120]}\n")
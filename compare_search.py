import json, sys
import numpy as np
from sentence_transformers import SentenceTransformer
from config import WINDOWS_FILE, EMBED_MODEL, IDS_FILE, embeddings_file

rows = [json.loads(line) for line in open(WINDOWS_FILE, encoding="utf-8")]
assert json.load(open(IDS_FILE)) == [r["window_id"] for r in rows], "re-run embed.py"
model = SentenceTransformer(EMBED_MODEL)

query = " ".join(sys.argv[1:])
q = model.encode("query: " + query, normalize_embeddings=True)
for variant in ["title", "notitle"]:
    scores = np.load(embeddings_file(variant)) @ q
    print(f"\n=== {variant} ===")
    for i in scores.argsort()[::-1][:5]:
        r = rows[i]
        print(f"{scores[i]:.3f}  {r['title'][:28]:28}  t={int(r['start']):>5}  {r['text'][:70]}")
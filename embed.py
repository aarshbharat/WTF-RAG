import json, time
import sys
import numpy as np
from sentence_transformers import SentenceTransformer
from config import WINDOWS_FILE, EMBED_MODEL, EMBEDDINGS_FILE, IDS_FILE, embeddings_file

rows = [json.loads(line) for line in open(WINDOWS_FILE, encoding="utf-8")]
variant = sys.argv[1] if len(sys.argv) > 1 else "title"
if variant == "title":
    texts = [f"passage: {r['title']} | {r['text']}" for r in rows]
else:
    texts = [f"passage: {r['text']}" for r in rows]

model = SentenceTransformer(EMBED_MODEL)
lengths = [len(ids) for ids in model.tokenizer(texts)["input_ids"]]
print(f"model reads up to {model.max_seq_length} tokens; longest window: {max(lengths)} tokens; "
      f"over the limit: {sum(n > model.max_seq_length for n in lengths)}")

t0 = time.time()
vecs = model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=True)
print(f"embedded {vecs.shape[0]} windows into {vecs.shape[1]} numbers each in {time.time() - t0:.0f}s")

np.save(embeddings_file(variant), vecs.astype(np.float32))
json.dump([r["window_id"] for r in rows], open(IDS_FILE, "w", encoding="utf-8"))
import json
import numpy as np
from qdrant_client import QdrantClient, models
from config import WINDOWS_FILE, IDS_FILE, QDRANT_PATH, COLLECTION, EMBED_VARIANT, embeddings_file

rows = [json.loads(line) for line in open(WINDOWS_FILE, encoding="utf-8")]
assert json.load(open(IDS_FILE)) == [r["window_id"] for r in rows], "re-run embed.py"
vecs = np.load(embeddings_file(EMBED_VARIANT))

client = QdrantClient(path=str(QDRANT_PATH))
if client.collection_exists(COLLECTION):
    client.delete_collection(COLLECTION)              # rebuild from scratch each run
client.create_collection(
    COLLECTION,
    vectors_config=models.VectorParams(size=vecs.shape[1], distance=models.Distance.COSINE),
)
client.upload_collection(COLLECTION, vectors=vecs, payload=rows,
                         ids=list(range(len(rows))), batch_size=256)
print(client.count(COLLECTION).count, "windows stored in Qdrant")
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/huggingface

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake the embedding model into the image so the container starts in seconds
# instead of downloading 470 MB on every cold start.
RUN python -c "from sentence_transformers import SentenceTransformer; \
SentenceTransformer('intfloat/multilingual-e5-small')"

COPY config.py rag.py server.py make_windows.py ./
COPY web/ ./web/
COPY data/qdrant/ ./data/qdrant/
COPY data/transcripts/ ./data/transcripts/
COPY data/playlist.json ./data/

ENV PORT=8080
EXPOSE 8080
# Shell form so ${PORT} expands at runtime. One worker only: local-mode Qdrant
# lets a single process hold the database lock.
CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1
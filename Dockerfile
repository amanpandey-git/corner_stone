# Synapse API (FastAPI + FAISS + bge-small, CPU only) for Google Cloud Run.
# The seven sample decks in samples/ are indexed while the image is built,
# so the hosted app starts with them already searchable.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    HF_HOME=/app/.hf_cache

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Downloads the embedding model into the image and builds data/ (index, page images).
RUN python -m cornerstone.cli ingest samples --yes

# At run time, use only the model already in the image.
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
CMD ["python", "deploy/start.py"]

"""Start the Synapse API on a host such as Google Cloud Run.

Adds the hosted web app's address (FRONTEND_URL, comma-separated if more than one) to the CORS
origins from config.yaml, then serves on $PORT. config.yaml itself is not changed.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cornerstone.api import create_app  # noqa: E402
from cornerstone.cli import load_config  # noqa: E402


def build_app(embedder=None):
    cfg = load_config()
    origins = cfg["api"].setdefault("cors_origins", [])
    for url in os.environ.get("FRONTEND_URL", "").split(","):
        url = url.strip().rstrip("/")
        if url and url not in origins:
            origins.append(url)
    return create_app(cfg) if embedder is None else create_app(cfg, embedder=embedder)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(build_app(), host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))

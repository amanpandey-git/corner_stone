"""Index manifest: records what the vectors in an index mean, and refuses a mismatch.

Vectors from different models (or dimensions, or metrics) are not comparable, so loading
an index with the wrong settings must fail loudly instead of returning garbage.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from cornerstone import ModelMismatch

INDEX_VERSION = 1
MANIFEST_NAME = "manifest.json"


@dataclass
class Manifest:
    model_name: str
    model_revision: str | None
    dimension: int
    space: str          # "cosine" (inner product on unit vectors)
    normalized: bool
    created_at: str
    index_version: int = INDEX_VERSION


def manifest_from_config(cfg: dict) -> Manifest:
    """Build the manifest a fresh index would get from the current config."""
    e, h = cfg["embedding"], cfg["hnsw"]
    return Manifest(
        model_name=e["model_name"], model_revision=e.get("model_revision"),
        dimension=e["dimension"], space=h["space"], normalized=bool(e["normalize"]),
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def manifest_path_for(index_path: Path) -> Path:
    """The manifest lives next to the index file."""
    return Path(index_path).with_name(MANIFEST_NAME)


def write_manifest(path: Path, m: Manifest) -> None:
    Path(path).write_text(json.dumps(asdict(m), indent=2), encoding="utf-8")


def read_manifest(path: Path) -> Manifest:
    """Raises ModelMismatch if the manifest is missing or unreadable (never guess)."""
    path = Path(path)
    if not path.is_file():
        raise ModelMismatch(f"manifest not found at {path}: cannot verify which model built this index")
    try:
        return Manifest(**json.loads(path.read_text(encoding="utf-8")))
    except (ValueError, TypeError) as e:
        raise ModelMismatch(f"manifest {path} is unreadable: {e}") from e


def check_manifest(m: Manifest, cfg: dict) -> None:
    """Raise ModelMismatch listing every difference between the index and the config."""
    want = manifest_from_config(cfg)
    problems = []
    for field in ("model_name", "model_revision", "dimension", "space", "normalized", "index_version"):
        have, need = getattr(m, field), getattr(want, field)
        if have != need:
            problems.append(f"{field}: index has {have!r}, config says {need!r}")
    if problems:
        raise ModelMismatch(
            "index was built with different settings (" + "; ".join(problems) + "). "
            "Re-index your documents or change config.yaml back."
        )

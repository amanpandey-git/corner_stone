"""HNSW vector index (faiss IndexHNSWFlat, inner product) with chunk_id as the label.

Why faiss and not hnswlib: no Windows wheel / no C++ compiler (see NOTES.md). The class
below is the only place that knows about faiss.

Deletion: faiss HNSW cannot remove vectors. Deleted chunks stay in the graph and are
filtered out by the caller using the SQLite `deleted` flag (see search.py).
"""
from __future__ import annotations

import os
from pathlib import Path

import faiss
import numpy as np

from cornerstone import ModelMismatch
from cornerstone.index.manifest import (Manifest, check_manifest, manifest_from_config,
                                        manifest_path_for, read_manifest, write_manifest)

_UNIT_TOLERANCE = 1e-3


class HNSWIndex:
    """Incremental HNSW index. Cosine similarity = inner product on unit-length vectors."""

    def __init__(self, manifest: Manifest, M: int, ef_construction: int, ef_search: int,
                 _loaded: faiss.IndexIDMap2 | None = None) -> None:
        self.manifest = manifest
        self.dim = manifest.dimension
        self.ef_search = ef_search
        if _loaded is not None:
            self._idmap = _loaded
            self._hnsw = faiss.downcast_index(_loaded.index)
        else:
            self._hnsw = faiss.IndexHNSWFlat(self.dim, M, faiss.METRIC_INNER_PRODUCT)
            self._idmap = faiss.IndexIDMap2(self._hnsw)  # labels = chunk_ids, not positions
        self._hnsw.hnsw.efConstruction = ef_construction

    # ------------------------------------------------------------ construction
    @classmethod
    def from_config(cls, cfg: dict) -> "HNSWIndex":
        """A new, empty index with the settings in config.yaml."""
        h = cfg["hnsw"]
        return cls(manifest_from_config(cfg), h["M"], h["ef_construction"], h["ef_search"])

    @classmethod
    def load(cls, path: Path, cfg: dict) -> "HNSWIndex":
        """Load index + manifest. Raises ModelMismatch if the manifest is missing or differs."""
        path = Path(path)
        manifest = read_manifest(manifest_path_for(path))
        check_manifest(manifest, cfg)
        if not path.is_file():
            raise ModelMismatch(f"manifest exists but index file {path} is missing")
        idmap = faiss.read_index(str(path))
        if idmap.d != manifest.dimension:
            raise ModelMismatch(f"index file has dimension {idmap.d}, manifest says {manifest.dimension}")
        h = cfg["hnsw"]
        return cls(manifest, h["M"], h["ef_construction"], h["ef_search"], _loaded=idmap)

    def save(self, path: Path) -> None:
        """Write index then manifest next to it. The index file is replaced atomically."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        faiss.write_index(self._idmap, str(tmp))
        os.replace(tmp, path)
        write_manifest(manifest_path_for(path), self.manifest)

    # ------------------------------------------------------------ use
    def __len__(self) -> int:
        return int(self._idmap.ntotal)

    def all_ids(self) -> np.ndarray:
        """Every label stored (including soft-deleted ones), for the SQLite sync check."""
        return faiss.vector_to_array(self._idmap.id_map).astype(np.int64)

    def vectors(self) -> tuple[np.ndarray, np.ndarray]:
        """(ids, matrix) of everything stored, in insertion order. Used by the ANN-vs-exact check."""
        n = len(self)
        if n == 0:
            return np.empty(0, dtype=np.int64), np.zeros((0, self.dim), dtype=np.float32)
        return self.all_ids(), self._hnsw.reconstruct_n(0, n)

    def add(self, ids: np.ndarray, vectors: np.ndarray) -> None:
        """Add vectors under the given labels. Never rebuilds; labels must be new and unique."""
        ids = np.asarray(ids, dtype=np.int64)
        vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        if vectors.ndim != 2 or vectors.shape[1] != self.dim:
            raise ValueError(f"expected vectors of shape (n, {self.dim}), got {vectors.shape}")
        if len(ids) != len(vectors):
            raise ValueError(f"{len(ids)} ids for {len(vectors)} vectors")
        if len(ids) == 0:
            return
        if len(np.unique(ids)) != len(ids) or (len(self) and np.isin(ids, self.all_ids()).any()):
            raise ValueError("ids must be unique and not already in the index (labels are never reused)")
        if not np.isfinite(vectors).all():
            raise ValueError("vectors contain NaN or inf")
        if np.abs(np.linalg.norm(vectors, axis=1) - 1.0).max() > _UNIT_TOLERANCE:
            raise ValueError("vectors must be L2-normalised (cosine space)")
        self._idmap.add_with_ids(vectors, ids)

    def search(self, query: np.ndarray, k: int, ef_search: int | None = None) -> tuple[np.ndarray, np.ndarray]:
        """Top-k (labels, scores), best first. Fewer than k if the index holds fewer vectors.

        ef is raised to at least k, because HNSW cannot return more results than it explores.
        Empty index -> two empty arrays.
        """
        if k < 1:
            raise ValueError("k must be >= 1")
        q = np.ascontiguousarray(query, dtype=np.float32).reshape(1, -1)
        if q.shape[1] != self.dim:
            raise ValueError(f"query has dimension {q.shape[1]}, index has {self.dim}")
        n = len(self)
        if n == 0:
            return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.float32)
        k = min(k, n)
        self._hnsw.hnsw.efSearch = max(ef_search or self.ef_search, k)
        scores, labels = self._idmap.search(q, k)
        keep = labels[0] != -1
        return labels[0][keep].astype(np.int64), scores[0][keep].astype(np.float32)

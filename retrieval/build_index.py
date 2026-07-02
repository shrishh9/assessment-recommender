"""Build a FAISS index over the cleaned SHL assessment catalog.

This module is responsible for:
- loading the cleaned assessments from data/assessments.json
- creating a text representation for each assessment
- generating embeddings with Sentence Transformers
- storing the embeddings in a FAISS index
- saving metadata that can be used at query time

The index can be regenerated easily whenever the catalog changes.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPO_ROOT / "data" / "assessments.json"
FAISS_INDEX_PATH = REPO_ROOT / "data" / "faiss.index"
METADATA_PATH = REPO_ROOT / "data" / "metadata.pkl"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_catalog(catalog_path: Path = CATALOG_PATH) -> List[Dict[str, Any]]:
    """Load the cleaned catalog from disk."""

    with catalog_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_text_representation(record: Dict[str, Any]) -> str:
    """Create a searchable text representation for one assessment."""

    parts: List[str] = []

    if record.get("name"):
        parts.append(record["name"])
    if record.get("description"):
        parts.append(record["description"])
    if record.get("test_type"):
        parts.append(f"test type: {record['test_type']}")
    if record.get("job_levels"):
        parts.append("job levels: " + ", ".join(record["job_levels"]))
    if record.get("languages"):
        parts.append("languages: " + ", ".join(record["languages"]))
    if record.get("duration"):
        parts.append(f"duration: {record['duration']}")
    if record.get("keys"):
        parts.append("keywords: " + ", ".join(record["keys"]))
    if record.get("status"):
        parts.append(f"status: {record['status']}")
    if record.get("adaptive"):
        parts.append(f"adaptive: {record['adaptive']}")
    if record.get("remote"):
        parts.append(f"remote: {record['remote']}")

    return " \n ".join(part for part in parts if part)


def build_index(
    catalog_path: Path = CATALOG_PATH,
    index_path: Path = FAISS_INDEX_PATH,
    metadata_path: Path = METADATA_PATH,
    model_name: str = EMBEDDING_MODEL_NAME,
) -> Tuple[int, List[Dict[str, Any]]]:
    """Build and persist the FAISS index and metadata."""

    records = load_catalog(catalog_path)
    texts = [build_text_representation(record) for record in records]

    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype("float32"))

    faiss.write_index(index, str(index_path))

    metadata = [
        {
            "id": record.get("id"),
            "name": record.get("name"),
            "url": record.get("url"),
            "description": record.get("description"),
            "test_type": record.get("test_type"),
            "job_levels": record.get("job_levels", []),
            "languages": record.get("languages", []),
            "duration": record.get("duration"),
            "keys": record.get("keys", []),
            "status": record.get("status"),
            "adaptive": record.get("adaptive"),
            "remote": record.get("remote"),
        }
        for record in records
    ]

    with metadata_path.open("wb") as handle:
        pickle.dump(metadata, handle)

    return len(records), metadata


if __name__ == "__main__":
    count, _ = build_index()
    print(f"Built FAISS index for {count} assessments")

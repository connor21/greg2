import os
import uuid
from pathlib import Path
from typing import List, Dict

import requests
import streamlit as st

from config import AppConfig


def ensure_dirs(cfg: AppConfig):
    cfg.DOCS_DIR.mkdir(parents=True, exist_ok=True)
    cfg.CACHE_DIR.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(docs_dir: Path, file) -> Path:
    ensure_dirs(AppConfig())
    dst = docs_dir / file.name
    with open(dst, "wb") as f:
        f.write(file.getbuffer())
    return dst


def list_documents(docs_dir: Path) -> List[Dict]:
    if not docs_dir.exists():
        return []
    items = []
    for p in sorted(docs_dir.iterdir()):
        if not p.is_file():
            continue
        items.append({
            "doc_id": p.stem,
            "filename": p.name,
        })
    return items


def delete_document_and_vectors(cfg: AppConfig, index, doc_meta: Dict):
    # Delete file
    path = cfg.DOCS_DIR / doc_meta.get("filename", "")
    try:
        if path.exists():
            path.unlink()
    except Exception as e:
        st.warning(f"Failed deleting file: {e}")
    # Delete vectors
    try:
        index.delete_by_doc(doc_meta.get("doc_id"))
    except Exception as e:
        st.warning(f"Failed deleting vectors: {e}")


def healthcheck_services(cfg: AppConfig) -> Dict[str, bool]:
    out = {"qdrant": False, "ollama": False}
    try:
        r = requests.get(f"{cfg.QDRANT_URL}/healthz", timeout=2)
        out["qdrant"] = r.ok
    except Exception:
        out["qdrant"] = False
    try:
        r = requests.get(f"{cfg.OLLAMA_HOST}/api/tags", timeout=2)
        out["ollama"] = r.ok
    except Exception:
        out["ollama"] = False
    return out


def list_ollama_models(cfg: AppConfig) -> List[str]:
    """Return a list of available Ollama model tags (names)."""
    try:
        r = requests.get(f"{cfg.OLLAMA_HOST}/api/tags", timeout=3)
        r.raise_for_status()
        data = r.json() or {}
        models = data.get("models", [])
        return [m.get("name") for m in models if isinstance(m, dict) and m.get("name")]
    except Exception:
        return []


def has_ollama_model(cfg: AppConfig, name: str) -> bool:
    """Return True if Ollama has a model locally (authoritative check via /api/show)."""
    try:
        payload = {"name": name}
        r = requests.post(f"{cfg.OLLAMA_HOST}/api/show", json=payload, timeout=4)
        return r.ok
    except Exception:
        return False

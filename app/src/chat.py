import json
from typing import Iterable, List, Dict
import requests

from app.src.config import AppConfig


def _build_system_prompt() -> str:
    return (
        "You are a helpful assistant that only answers using the provided documents. "
        "If the answer is not in the documents, say: 'Ich konnte die Antwort in den Dokumenten nicht finden.' "
        "Always cite sources as (doc, page) when available."
    )


def _context_from_chunks(chunks: List[Dict]) -> str:
    parts = []
    for c in chunks:
        doc = c.get("doc")
        page = c.get("page")
        txt = c.get("text", "")
        header = f"Source: {doc or 'unknown'} | Page: {page if page is not None else '?'}"
        parts.append(f"[{header}]\n{txt}")
    return "\n\n---\n\n".join(parts)


def chat_stream(cfg: AppConfig, question: str, retrieved: List[Dict]) -> Iterable[str]:
    url = f"{cfg.OLLAMA_HOST}/api/chat"
    headers = {"Content-Type": "application/json"}

    context = _context_from_chunks(retrieved)
    payload = {
        "model": cfg.LLM_MODEL,
        "stream": True,
        "messages": [
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        "options": {
            "temperature": 0.2,
        },
    }

    with requests.post(url, headers=headers, data=json.dumps(payload), stream=True, timeout=600) as r:
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue
            chunk = data.get("message", {}).get("content")
            if chunk:
                yield chunk

from typing import List, Dict

import tiktoken


def _estimate_tokens(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def chunk_text(text: str, chunk_size_tokens: int = 600, chunk_overlap_tokens: int = 80) -> List[Dict]:
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append({
            "text": chunk_text,
            "tokens": len(chunk_tokens),
        })
        if end == len(tokens):
            break
        start = end - chunk_overlap_tokens
        if start < 0:
            start = 0
    return chunks

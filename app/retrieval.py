from typing import List, Dict

from FlagEmbedding import FlagReranker

from embeddings import get_embedder

# Lazy singleton reranker
_reranker = None


def _get_reranker(model_name: str) -> FlagReranker:
    global _reranker
    if _reranker is None:
        _reranker = FlagReranker(model_name, use_fp16=True)
    return _reranker


def retrieve_with_rerank(cfg, index, query: str, top_k: int = 30, top_n: int = 6) -> List[Dict]:
    embedder = get_embedder(cfg.EMBEDDING_MODEL)
    candidates = index.search(embedder, query, top_k=top_k)
    if not candidates:
        return []
    reranker = _get_reranker(cfg.RERANK_MODEL)
    pairs = [[query, c["text"]] for c in candidates]
    scores = reranker.compute_score(pairs)
    for c, s in zip(candidates, scores):
        c["rerank_score"] = float(s)
    candidates.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
    return candidates[:top_n]

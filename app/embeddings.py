from typing import List

from FlagEmbedding import BGEM3FlagModel

# Lazy singleton to avoid reloading the model repeatedly
_embedder = None


def get_embedder(model_name: str = "BAAI/bge-m3") -> BGEM3FlagModel:
    global _embedder
    if _embedder is None:
        _embedder = BGEM3FlagModel(model_name, use_fp16=True)
    return _embedder


def embed_texts(embedder: BGEM3FlagModel, texts: List[str]) -> List[List[float]]:
    # BGEM3 returns dict with 'dense_vecs'
    out = embedder.encode(texts, return_dense=True, return_sparse=False, return_colbert_vecs=False)
    return out["dense_vecs"].tolist() if hasattr(out["dense_vecs"], "tolist") else out["dense_vecs"]


def embed_query(embedder: BGEM3FlagModel, text: str) -> List[float]:
    return embed_texts(embedder, [text])[0]

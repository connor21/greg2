from typing import List, Dict, Optional
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, Filter, FieldCondition, MatchValue, PointStruct
import uuid

from app.src.embeddings import embed_texts


@dataclass
class VectorIndex:
    qdrant_url: str
    collection: str
    embedding_model: str

    def __post_init__(self):
        self.client = QdrantClient(url=self.qdrant_url)
        self._dim: Optional[int] = None
        # Do not create collection until we know vector dim. Will lazy-create on first add.

    def _ensure_collection(self, dim: int):
        self._dim = dim
        collections = self.client.get_collections().collections
        names = {c.name for c in collections}
        if self.collection not in names:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

    def add_documents(self, embedder, chunks: List[Dict], base_meta: Dict):
        texts = [c["text"] for c in chunks]
        vectors = embed_texts(embedder, texts)
        if self._dim is None:
            self._ensure_collection(len(vectors[0]))
        points: List[PointStruct] = []
        for c, v in zip(chunks, vectors):
            payload = {
                "doc_id": base_meta.get("doc_id"),
                "filename": base_meta.get("filename"),
                "page": c.get("page"),
                "tokens": c.get("tokens"),
                "text": c.get("text"),
                "hash": base_meta.get("hash"),
            }
            points.append(PointStruct(id=str(uuid.uuid4()), vector=v, payload=payload))
        self.client.upsert(collection_name=self.collection, points=points)

    def delete_by_doc(self, doc_id: str):
        self.client.delete(
            collection_name=self.collection,
            filter=Filter(must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]),
        )

    def search(self, embedder, query: str, top_k: int = 30) -> List[Dict]:
        qvec = embed_texts(embedder, [query])[0]
        # Ensure collection exists even if user searches before indexing any docs
        try:
            collections = self.client.get_collections().collections
            names = {c.name for c in collections}
            if self.collection not in names:
                self._ensure_collection(len(qvec))
        except Exception:
            # If listing collections fails, attempt to create with inferred dim
            self._ensure_collection(len(qvec))
        res = self.client.search(
            collection_name=self.collection,
            query_vector=qvec,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )
        out = []
        for r in res:
            pl = r.payload or {}
            out.append({
                "text": pl.get("text", ""),
                "doc": pl.get("filename"),
                "doc_id": pl.get("doc_id"),
                "page": pl.get("page"),
                "score": r.score,
            })
        return out

import os
import uuid
import time
from pathlib import Path
from typing import List, Dict
import sys

# Ensure this directory (app/) is on sys.path so local module imports work
_FILE_DIR = Path(__file__).resolve().parent
if str(_FILE_DIR) not in sys.path:
    sys.path.insert(0, str(_FILE_DIR))

import streamlit as st
from dotenv import load_dotenv

from config import AppConfig
from parsers import parse_document
from chunker import chunk_text
from embeddings import get_embedder
from vectorstore import VectorIndex
from retrieval import retrieve_with_rerank
from chat import chat_stream
from utils import (
    list_documents,
    save_uploaded_file,
    delete_document_and_vectors,
    healthcheck_services,
    ensure_dirs,
    list_ollama_models,
    has_ollama_model,
)


def init_state():
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "index" not in st.session_state:
        st.session_state["index"] = None


def init_index(cfg: AppConfig) -> VectorIndex:
    if st.session_state.get("index") is None:
        st.session_state["index"] = VectorIndex(
            qdrant_url=cfg.QDRANT_URL,
            collection=cfg.COLLECTION_NAME,
            embedding_model=cfg.EMBEDDING_MODEL,
        )
    return st.session_state["index"]


def ui_sidebar(cfg: AppConfig, index: VectorIndex):
    st.sidebar.header("Documents")
    docs = list_documents(cfg.DOCS_DIR)
    if docs:
        st.sidebar.write(f"{len(docs)} file(s)")
        for d in docs:
            with st.sidebar.expander(d["filename"], expanded=False):
                st.caption(f"ID: {d['doc_id']}")
                st.caption(f"Pages: {d.get('pages','?')}")
                col1, col2 = st.columns(2)
                if col1.button("Reindex", key=f"re_{d['doc_id']}"):
                    try:
                        file_path = cfg.DOCS_DIR / d["filename"]
                        with st.spinner("Reindexing…"):
                            process_and_index(cfg, index, file_path)
                        st.success("Reindexed")
                    except Exception as e:
                        st.error(f"Failed to reindex: {e}")
                if col2.button("Delete", key=f"del_{d['doc_id']}"):
                    delete_document_and_vectors(cfg, index, d)
                    st.experimental_rerun()
    else:
        st.sidebar.info("No documents yet.")

    st.sidebar.divider()
    st.sidebar.subheader("Services")
    hc = healthcheck_services(cfg)
    st.sidebar.write(
        f"Qdrant: {'✅' if hc['qdrant'] else '❌'} | Ollama: {'✅' if hc['ollama'] else '❌'}"
    )

    # Models info
    st.sidebar.subheader("Models")
    model_name = (cfg.LLM_MODEL or "").strip()
    st.sidebar.write(f"LLM model: {model_name}")
    try:
        if model_name and has_ollama_model(cfg, model_name):
            st.sidebar.success("Ollama has this model")
        else:
            available = list_ollama_models(cfg)
            st.sidebar.warning("Model not installed in Ollama yet")
            if available:
                st.sidebar.caption("Available: " + ", ".join(available))
            else:
                st.sidebar.info("Could not list Ollama models")
    except Exception as e:
        st.sidebar.info(f"Model check skipped: {e}")


def process_and_index(cfg: AppConfig, index: VectorIndex, file_path: Path) -> Dict:
    text, meta = parse_document(file_path)
    chunks: List[Dict] = []
    # Page-aware chunking for proper citations
    page_texts = meta.get("page_texts")
    if page_texts:
        for pt in page_texts:
            page_chunks = chunk_text(
                pt.get("text", ""),
                chunk_size_tokens=cfg.CHUNK_SIZE_TOKENS,
                chunk_overlap_tokens=cfg.CHUNK_OVERLAP_TOKENS,
            )
            for ch in page_chunks:
                ch["page"] = pt.get("page")
            chunks.extend(page_chunks)
    else:
        chunks = chunk_text(
            text,
            chunk_size_tokens=cfg.CHUNK_SIZE_TOKENS,
            chunk_overlap_tokens=cfg.CHUNK_OVERLAP_TOKENS,
        )
    embedder = get_embedder(cfg.EMBEDDING_MODEL)
    index.add_documents(embedder, chunks, base_meta=meta)
    return {"chunks": len(chunks), **meta}


def main():
    load_dotenv(os.getenv("ENV_FILE", ".env"), override=False)
    cfg = AppConfig()

    init_state()
    ensure_dirs(cfg)
    st.set_page_config(page_title="Local RAG Chat", page_icon="💬", layout="wide")

    st.title("Local RAG Chat 💬")
    st.write("Upload documents and chat with them. Supports PDF/DOCX/TXT/MD. Runs fully local.")

    index = init_index(cfg)
    ui_sidebar(cfg, index)

    # Upload section
    st.subheader("Upload a document")
    up = st.file_uploader("Choose a file", type=["pdf", "docx", "txt", "md"])
    if up is not None:
        saved_path = save_uploaded_file(cfg.DOCS_DIR, up)
        with st.status("Indexing...", expanded=True) as status:
            st.write("Parsing…")
            try:
                info = process_and_index(cfg, index, saved_path)
                st.write(f"Parsed {info.get('pages','?')} pages. Creating chunks & embeddings…")
                st.write(f"Stored into collection '{cfg.COLLECTION_NAME}'.")
                status.update(label="Indexing complete", state="complete")
            except Exception as e:
                st.error(f"Failed to index: {e}")

    st.divider()

    # Chat section
    st.subheader("Chat")
    user_q = st.text_input("Ask a question about your documents")
    if st.button("Ask", type="primary") and user_q:
        with st.spinner("Retrieving…"):
            retrieved = retrieve_with_rerank(
                cfg, index, user_q, top_k=cfg.TOP_K, top_n=cfg.TOP_N
            )
        st.session_state["messages"].append({"role": "user", "content": user_q})

        st.write("Generating…")
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full = ""
            for chunk in chat_stream(cfg, user_q, retrieved):
                full += chunk
                placeholder.markdown(full)
            # Append citations at end
            cites = []
            for r in retrieved:
                doc = r.get("doc")
                pg = r.get("page")
                if doc is not None and pg is not None:
                    cites.append(f"({doc}, p.{pg})")
            if cites:
                placeholder.markdown(full + "\n\n" + "Sources: " + ", ".join(cites))
            with st.expander("Show sources"):
                for i, r in enumerate(retrieved, 1):
                    st.markdown(f"**{i}. {r.get('doc')} — p.{r.get('page')}**")
                    st.code(r.get("text", ""), language="markdown")
        st.session_state["messages"].append({"role": "assistant", "content": full})

    # Show history
    for m in st.session_state["messages"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])


if __name__ == "__main__":
    main()

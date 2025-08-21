# Local RAG Chat — Linux Setup

A local RAG (Retrieval-Augmented Generation) chat app built with Streamlit, Qdrant (vector DB), and Ollama (local LLM). Supports PDF/DOCX/TXT/MD, creates embeddings with FlagEmbedding, and does reranking.

## Features
- Fully local pipeline: embeddings, vector search (Qdrant), reranking, and LLM via Ollama
- Streamlit UI to upload docs and chat with citations
- Docker Compose for one-command start

## Requirements (Linux)
- Docker and Docker Compose
- Or: Python 3.11+ if running natively

## Quick Start (Docker Compose)
1. Clone and enter directory
   ```bash
   git clone <YOUR_REPO_URL> rag-app && cd rag-app
   ```
2. Create env file (optional; defaults are sensible). You can start from `example.env`:
   ```bash
   cp example.env .env
   ```
   Adjust values if needed (e.g., `LLM_MODEL`, `EMBEDDING_MODEL`).
3. Start services
   ```bash
   docker compose up --build
   ```
   - Services: `app` (Streamlit), `qdrant`, `ollama`
   - Ports: Streamlit `8501`, Qdrant `6333`, Ollama `11434`
   - First run will auto-pull the LLM model defined by `LLM_MODEL`.
4. Open the app
   - http://localhost:8501

### Data and volumes
- App mounts project into container for live reload (`./:/app`).
- Data root defaults to `./data` and is mounted to `/data` inside the container.
  - Docs you upload are stored under `data/docs/`.
  - Qdrant data is persisted under `data/qdrant/`.
  - Ollama data is persisted under `data/ollama/`.

## Native Linux (without Docker)
Run Qdrant and Ollama yourself, then start the Streamlit app.

1. Install system deps (example for Debian/Ubuntu):
   ```bash
   sudo apt-get update && sudo apt-get install -y python3.11-venv python3-pip git curl build-essential
   ```
2. Create and activate a venv
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   ```
3. Install Python deps
   ```bash
   pip install -r requirements.txt
   ```
4. Start Qdrant
   - Easiest with Docker:
     ```bash
     docker run -p 6333:6333 -v $(pwd)/data/qdrant:/qdrant/storage qdrant/qdrant:latest
     ```
   - Or install Qdrant natively (see Qdrant docs).
5. Start Ollama and pull a model
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama serve &
   ollama pull llama3.1:8b   # or any model you set in .env
   ```
6. Configure environment
   ```bash
   cp example.env .env   # optional; edit as desired
   ```
   For native run, typical values:
   ```env
   QDRANT_URL=http://localhost:6333
   OLLAMA_HOST=http://localhost:11434
   DATA_ROOT=./data
   ```
7. Run the app
   ```bash
   export ENV_FILE=.env
   streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0
   ```
   Open http://localhost:8501

## Environment variables
See `example.env` for a complete set. Key ones:
- QDRANT_URL: default `http://localhost:6333` (Docker: `http://qdrant:6333`)
- OLLAMA_HOST: default `http://localhost:11434` (Docker: `http://ollama:11434`)
- DATA_ROOT: path to data root (default `./data`)
- COLLECTION_NAME: Qdrant collection name (default `docs`)
- LLM_MODEL: Ollama model tag, e.g., `llama3.1:8b` or `qwen2.5:3b`
- EMBEDDING_MODEL: default `BAAI/bge-m3`
- RERANK_MODEL: default `BAAI/bge-reranker-base`
- CHUNK_SIZE_TOKENS, CHUNK_OVERLAP_TOKENS, TOP_K, TOP_N: retrieval params

The app loads `.env` via `ENV_FILE` (default `.env`), see `app/main.py` and `app/src/config.py`.

## Usage
- Upload PDF/DOCX/TXT/MD via the UI.
- Ask questions; answers show citations and source chunks.
- Manage documents in the sidebar: Reindex or Delete.

## Troubleshooting
- Ollama model missing: run `ollama pull <model>` or ensure `LLM_MODEL` is correct.
- Ports busy: stop other services or change ports in `docker-compose.yml`.
- Qdrant not reachable: verify container logs, or `curl http://localhost:6333/healthz`.
- Permissions on `data/`: ensure your user can read/write `data/`.
- GPU vs CPU: This setup uses CPU by default; configure Ollama or base images for GPU if desired.

## Development
- The container mounts the repo, so code changes reload Streamlit.
- Python path is set to `/app` in Docker; modules live under `app/`.

## License
Your project license here.

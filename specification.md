# 1) Overview

A Streamlit web app where users upload documents (PDF/DOCX/TXT/MD), the system indexes them into a local RAG pipeline, and users chat in German or English with citations back to the sources. Runs on a **single server** (CPU or 1×GPU), minimal services, low ops overhead.

**Guiding principles**

* “Simple, but not simpler”
* Prefer well‑tested, lightweight components
* Local‑first (no external SaaS required)

---

# 2) Toolstack (final choices)

**UI**

* **Streamlit** – fast UI, chat interface, file upload, session state.

**RAG Orchestration**

* **LlamaIndex** – clean ingestion/retrieval pipelines, citation support, composable.

**LLM Runtime**

* **Ollama** running **Llama‑3.1‑8B‑Instruct** (primary)

  * Reason: one‑binary runtime, easy model mgmt, good DE/EN, CPU/GPU capable.
  * Alternative fallback (only if needed later): llama.cpp directly.

**Embeddings**

* **bge‑m3** (FlagEmbedding) – multilingual, strong retrieval (DE/EN), CPU‑friendly.

**Reranker**

* **bge‑reranker‑base** – lightweight cross‑encoder to refine top‑K → top‑N.

**Vector Store**

* **Qdrant** (single Docker container; persistent volume) – stable, fast, filters/metadata.

**Parsing / OCR**

* **PyMuPDF** for PDFs (fast, reliable)
* **python‑docx**, built‑in readers for TXT/MD
* **Tesseract OCR** (lang packs `eng`, `deu`) – **optional** for scanned PDFs (toggle in UI)

**Storage**

* Local filesystem:

  * `/data/docs` (raw files)
  * `/data/qdrant` (vector store)
  * `/data/cache` (artifacts, chunks)

**Config & Security**

* **python‑dotenv** for secrets/config
* **streamlit‑authenticator** (optional) for basic username/password login

**Observability (minimal by default)**

* Structured app logs (JSON), latency counters, retrieval size
* (Optional later) **Langfuse** for traces

**Packaging**

* **Docker Compose** with **3 services**: `app` (Streamlit), `qdrant`, `ollama`

---

# 3) Architecture

**Topology (single server)**

* **Streamlit App (Python)**

  * Hosts UI, ingestion jobs, RAG pipeline orchestration with LlamaIndex
  * Talks to **Ollama** (HTTP) for LLM inference
  * Talks to **Qdrant** (HTTP) for vector search
  * Reads/writes local filesystem for documents & artifacts

**Request/Data Flow**

1. **Upload** → Streamlit saves file → parse (PyMuPDF / docx / txt) → (optional OCR)
2. **Chunk** → token/semantic splitter (300–800 tokens) + metadata (doc\_id, page, lang)
3. **Embed** → bge‑m3 → vectors + metadata → Qdrant collection
4. **Query** → retrieve top‑K (e.g., 30) from Qdrant → **rerank** with bge‑reranker‑base → keep 6–8
5. **Generate** → context‑stuffed prompt to Llama‑3.1‑8B via Ollama → stream tokens to UI
6. **Citations** → include (doc, page, snippet) from chunk metadata

**Key Parameters (defaults)**

* Chunk size: \~600 tokens, 60–100 tokens overlap
* Retrieval: `top_k=30` → rerank → `top_n=6–8`
* Max context fed to LLM: \~4–6k tokens (pragmatic for 8B model)
* Language: auto‑detect per user message; mirror user language in responses

**Security & Access**

* Optional login; per‑session document scoping (user‑local collections)
* No multi‑tenant isolation beyond per‑user collections in this first iteration
* File deletion evicts vectors + artifacts for the deleted doc

---

# 4) Data Model (metadata essentials)

**Document**

* `doc_id` (UUID), `filename`, `mime`, `uploaded_by`, `uploaded_at`, `language_guess`, `hash`

**Chunk**

* `chunk_id`, `doc_id`, `text`, `page`, `section_heading?`, `tokens`, `language`
* `embedding` (vector), `created_at`

**Chat Message**

* `session_id`, `role` (user/assistant), `ts`, `question`, `answer`, `citations[]`

---

# 5) Deployment (single‑server)

**docker‑compose.yml (sketch)**

* `app`: Streamlit + Python deps; mounts `/data`
* `qdrant`: persistent volume `/data/qdrant`
* `ollama`: persistent model cache; pre‑pull `llama3.1:8b`
* Healthchecks for qdrant & ollama before app starts

**Resources**

* CPU‑only OK (slower); 1×GPU (12–16GB) recommended for snappy responses
* Disk: plan \~2–3× source size for artifacts + vectors

**Config**

* `.env`: model names, chunk sizes, retrieval params, path roots, auth toggle

---

# 6) Non‑Functional Requirements

* **Performance**: p50 answer latency ≤ 4–6s on small docs with GPU; CPU: ≤ 10–15s target
* **Accuracy**: answers always cite sources; if not found, say “not in documents”
* **Stability**: restart‑safe; no data loss (volumes mounted)
* **Simplicity**: ≤ 3 containers; minimal knobs exposed in UI
* **i18n**: DE/EN—echo user language; support German diacritics and OCR (`deu`)

---

# 7) High‑Level Features (Epics)

### Epic A — Document Ingestion & Management

**Goal:** Bring documents into the system, parse, index, and manage them.
**Includes:**

* Upload multiple files (PDF/DOCX/TXT/MD)
* Parse + (optional) OCR scans
* Chunking + metadata
* Embedding → Qdrant
* List, delete, re‑index documents
* Show processing progress and failures

### Epic B — Chat with Documents

**Goal:** Natural‑language Q\&A over indexed docs with citations.
**Includes:**

* Chat UI with streaming responses
* Retrieval (top‑K) + reranking (top‑N)
* Context‑stuffed generation via Ollama
* Citations (doc name + page + snippet)
* Follow‑up question suggestions
* Scope chat to “all docs” or selected subset

### Epic C — Quality & Controls

**Goal:** Keep answers grounded and controllable.
**Includes:**

* “Show sources” toggle & snippet previews
* “Only answer from docs” mode (refuse unsupported claims)
* Basic answer feedback (👍/👎) stored locally
* Rate limits to protect server

### Epic D — User & Session Management

**Goal:** Lightweight access control and session continuity.
**Includes:**

* Optional login (streamlit‑authenticator)
* Per‑session chat history
* Export chat transcript (TXT/MD)

### Epic E — Operations & Observability (Minimal)

**Goal:** Basic operational visibility and safe operation.
**Includes:**

* Structured logging (ingestion, retrieval, generation)
* Simple metrics: request count, latency p50/p95, token usage
* Healthchecks for Ollama/Qdrant
* Admin page: service status, storage usage, reindex all

### Epic F — Internationalization (DE/EN)

**Goal:** Smooth bilingual operation.
**Includes:**

* Auto language detection for user queries
* Answer in user language
* OCR language switch (eng/deu)

---

# 8) Out of Scope (initial release)

* Multi‑tenant enterprise RBAC/SSO
* Fine‑grained ACL per document section
* Advanced eval dashboards (e.g., Ragas) and prompt A/B testing
* Non‑textual extraction (tables/figures layout capture beyond plain text)
* External SaaS vector stores or LLMs

---

# 9) Risks & Mitigations

* **Scanned PDFs degrade quality** → Provide OCR toggle; flag low‑confidence pages.
* **Large docs slow ingestion** → Background job runner in‑process; progress UI; chunk size caps.
* **CPU‑only latency** → Offer “concise mode” (shorter max tokens) and smaller reranker/LLM knobs.
* **Hallucinations** → “Only from docs” mode; enforce citations; instructive system prompt.

---

# 10) Milestones

1. **MVP (Weeks 1–2)**: Ingest (PDF/DOCX/TXT), retrieval + citations, chat UI, delete/reindex, single collection.
2. **Polish (Weeks 3–4)**: OCR option, reranker, doc scoping, transcripts, minimal metrics.
3. **Ops (Week 5)**: Admin page, healthchecks, volumes, backup script.
4. **Nice‑to‑have (later)**: Langfuse tracing, batch import, folders/tags, evaluation set.

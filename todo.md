Got it 👍 — here’s the same **TODO list** as plain GitHub-style checklists with acceptance criteria, no tables:

---

# 📋 Project TODO with Acceptance Criteria

### **Milestone 1 – MVP (Weeks 1–2)**

* [x] **Set up project scaffold**

  * Acceptance: `docker-compose up` starts `app`, `qdrant`, `ollama`; healthcheck confirms Qdrant + Ollama reachable.
* [x] **Implement Streamlit landing page**

  * Acceptance: User sees header + description; can upload a file; file is saved to `/data/docs`.
* [x] **Document parser integration**

  * Acceptance: Upload PDF/DOCX/TXT → plain text extracted; extraction shows correct characters/pages.
* [x] **Chunking pipeline**

  * Acceptance: Docs are split into \~600 token chunks; chunks stored with doc\_id + page metadata.
* [x] **Embedding + Qdrant index**

  * Acceptance: Embeddings created with bge-m3; ≥90% chunks stored in Qdrant without error.
* [x] **Simple retrieval + rerank**

  * Acceptance: Query returns ranked chunks; same query returns consistent top snippet.
* [x] **Chat UI + response streaming**

  * Acceptance: User types a question → model answers; tokens stream into UI progressively.
* [x] **Citations in answers**

  * Acceptance: Each answer shows `(doc, page)` citations; clicking reveals snippet text.
* [x] **Delete/reindex doc**

  * Acceptance: Deleted doc removed from doc list; retrieval returns no references to it.

---

### **Milestone 2 – Polish (Weeks 3–4)**

* [ ] **OCR support for scanned PDFs**

  * Acceptance: OCR extracts text from scanned PDFs with `eng/deu`; toggle works.
* [ ] **Document scoping (filters)**

  * Acceptance: User can query “all docs” or specific doc(s); retrieval respects scope.
* [ ] **Transcript export**

  * Acceptance: “Download chat” exports full Q\&A (TXT/MD) with timestamps + citations.
* [ ] **Answer feedback buttons**

  * Acceptance: User can click 👍/👎 once per answer; feedback stored in local JSON log.
* [ ] **Minimal metrics & logs**

  * Acceptance: Logs show ingestion + query latency; metrics endpoint returns counts + latency p50/p95.

---

### **Milestone 3 – Ops (Week 5)**

* [ ] **Admin page**

  * Acceptance: Sidebar shows doc count, chunk count, disk usage, and service status.
* [ ] **Healthchecks**

  * Acceptance: If Qdrant or Ollama is down, app shows a warning banner.
  * Note: Status indicators (✅/❌) are implemented in the sidebar; warning banner behavior pending.
* [x] **Persistent storage**

  * Acceptance: `/data/docs`, `/data/qdrant`, `/data/cache` survive container restarts.
* [ ] **Backup script**

  * Acceptance: Running `./backup.sh` creates a timestamped archive; restoring re-enables docs.

---

### **Milestone 4 – Nice-to-have (Later)**

* [ ] **Langfuse integration**

  * Acceptance: Each chat turn is logged as a trace in Langfuse UI.
* [ ] **Batch import folder of docs**

  * Acceptance: Importing a folder indexes all files inside; all docs appear in UI.
* [ ] **Tags/folders for docs**

  * Acceptance: User can assign tags during upload; chat filter allows scoping by tag.

---

👉 Do you want me to also **group these into GitHub Project “Issues” format** (with labels for milestone, e.g. `m1-mvp`, `m2-polish`)? That way they’re ready to paste into GitHub Issues via copy/paste.

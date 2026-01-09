# Copilot / AI Agent Instructions — RAG Chatbot

Purpose: give an AI coding agent the minimal, actionable context to be immediately productive in this repository.

- **Big picture**: This repo implements an on-prem RAG pipeline: document ingestion -> chunking -> Chroma vector DB -> retrieval + Ollama LLM for answers.
  - Ingestion: `load_data.py` (robust PDF+DOCX, OCR, table extraction) and `vector.py` (simpler PDF-focused loader).
  - Runtime: `api.py` (FastAPI endpoints for queries) and `chat.py` (Streamlit UI with streaming LLM responses).
  - Persistent DB: `./chroma_langchain_db` (Chroma, created/loaded by ingestion scripts).

- **Key files to read first**:
  - `load_data.py` — canonical ingestion: hybrid OCR (EasyOCR), pdfplumber, PyMuPDF, DOCX table extraction, chunk id scheme.
  - `vector.py` — alternative/simpler ingestion flow (useful for smaller test cases).
  - `api.py` — FastAPI endpoints: `/query`, `/query/simple`, `/stats`; lazy DB init via `get_db()`.
  - `chat.py` — Streamlit front-end using `ChatOllama` and `OllamaEmbeddings`.

- **Important conventions & patterns (do not change lightly)**:
  - Data lives on Windows path `D:\RAG\data` (variable `data_path` in loaders). Ingress scripts expect PDFs/DOCX there.
  - Chroma DB path is `./chroma_langchain_db` (vars: `CHROMA_PATH` / `db_location`).
  - Metadata canonical keys: `source`, `page`, `type`, `id`, `total_pages`, `has_table`, `used_ocr`, `file_type`.
  - Chunking: regular text uses chunk_size=1000/overlap=200; table-containing sections use chunk_size=2000/overlap=100 to keep tables intact.
  - ID scheme: `{source}:{file_type}:page_{n}{_table}{_ocr}:chunk_{i}` (see `calculate_chunk_ids` in loaders).
  - Embedding model string: `embeddinggemma` (Ollama embeddings). LLM: `llama3.1:8b` or `llama3.2` (used in `chat.py` / `api.py`).

- **Dev workflows & commands**:
  - Build/ingest data (create/update Chroma DB):
    - `python load_data.py` (options: `--reset` to clear DB, `--test` for quick checks)
    - or `python vector.py` for the simpler loader
  - Run API server locally:
    - `python api.py` (starts `uvicorn` with reload) or `uvicorn api:app --reload --host 0.0.0.0 --port 8000`.
  - Run Streamlit UI:
    - `streamlit run chat.py`
  - Typical debugging checkpoints: confirm `data_path` exists and contains PDFs/DOCX; check `./chroma_langchain_db` permissions; verify Ollama daemon/models are available.

- **Integration & dependencies to verify**:
  - Native modules: `fitz` (PyMuPDF), `pdfplumber`, `python-docx`, `easyocr` (or optional `pytesseract`), `Pillow`, `numpy`.
  - LangChain wrappers: `langchain_chroma`, `langchain_ollama`, `langchain_core` and community utilities used in code.
  - External service: Ollama (local model runtime) must be reachable and host correct models named above.

- **Behavioral guidance for edits**:
  - Preserve metadata keys and ID format — other components rely on them for dedup/upsert checks.
  - Keep table-handling chunk sizes intact; merging tables into smaller chunks breaks retrieval fidelity.
  - When changing DB path or data path, update both loader(s) and `api.py` / `chat.py` variables.

- **Examples (use these when writing code/tests):**
  - Sample chunk ID: `MyFile.pdf:pdf:page_3_table_ocr:chunk_0`
  - Example health call: `GET http://localhost:8000/health` returns `database: connected` when Chroma initialized.
  - Retrieval flow: `db.similarity_search_with_score(query, k)` → build prompt from results → `Ollama.invoke()` or `ChatOllama.stream()`.

If anything is unclear or you want more examples (unit tests, CI steps, or a short README), tell me which section to expand. 

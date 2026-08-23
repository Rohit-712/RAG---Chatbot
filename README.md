# RAG Chatbot

A full-stack Retrieval-Augmented Generation chatbot: upload documents (PDF/TXT/MD),
they get chunked and embedded into a vector store, and a chat interface answers
questions grounded in that content — with per-user auth and persisted chat history.

## Architecture

```
┌─────────────┐      REST/JSON       ┌──────────────────────────────────────┐
│  Frontend   │ ───────────────────► │              FastAPI backend           │
│ (HTML/JS)   │ ◄─────────────────── │                                        │
└─────────────┘                      │  routes: auth / upload / chat         │
                                      │  services: rag_pipeline               │
                                      │      ├─ embeddings (sentence-transf.) │
                                      │      ├─ vector_store (ChromaDB)       │
                                      │      └─ llm (OpenAI chat completions) │
                                      │  db: SQLite (users, chat history)     │
                                      └──────────────────────────────────────┘
```

**Flow:**
1. User registers/logs in → receives a JWT.
2. User uploads a PDF/TXT/MD → text extracted → split into overlapping chunks
   → embedded locally (sentence-transformers) → stored in ChromaDB, scoped to
   that user.
3. User asks a question → query embedded → top-k similar chunks retrieved →
   chunks + recent chat history sent to the LLM → grounded answer returned
   along with the source chunks used.
4. Every turn is persisted to SQLite so history survives reloads.

## Tech stack

| Layer          | Choice                                   |
|----------------|-------------------------------------------|
| API framework  | FastAPI                                   |
| Auth           | JWT (python-jose) + bcrypt (passlib)      |
| Relational DB  | SQLite via SQLAlchemy (swap-in Postgres)  |
| Vector store   | ChromaDB (persisted locally)              |
| Embeddings     | sentence-transformers (`all-MiniLM-L6-v2`)|
| LLM            | OpenAI Chat Completions (`gpt-4o-mini`)   |
| Frontend       | Vanilla HTML/CSS/JS (no build step)       |
| Containerized  | Docker + docker-compose                   |

## Project structure

```
rag-chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, router wiring, startup
│   │   ├── config.py          # Settings (env-driven)
│   │   ├── routes/
│   │   │   ├── auth.py        # /auth/register, /auth/login
│   │   │   ├── upload.py      # /upload  (ingest a document)
│   │   │   └── chat.py        # /chat, /chat/history/{session_id}
│   │   ├── services/
│   │   │   ├── rag_pipeline.py# orchestrates ingest + retrieve + generate
│   │   │   ├── embeddings.py  # sentence-transformers wrapper
│   │   │   ├── vector_store.py# ChromaDB wrapper
│   │   │   └── llm.py         # OpenAI chat completion wrapper
│   │   ├── models/
│   │   │   ├── user.py        # SQLAlchemy User model
│   │   │   └── chat_history.py# ChatMessage + Document models
│   │   ├── db/
│   │   │   ├── database.py    # engine/session/init_db
│   │   │   └── schema.py      # Pydantic request/response schemas
│   │   └── utils/
│   │       ├── pdf_loader.py  # PDF/TXT/MD text extraction
│   │       ├── chunking.py    # sentence-aware overlapping chunker
│   │       └── security.py    # password hashing + JWT helpers
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── docker-compose.yml
└── README.md
```

## Running it

### Option A — Docker Compose (recommended)

```bash
cp backend/.env.example backend/.env   # fill in OPENAI_API_KEY at minimum
docker compose up --build
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:5500

### Option B — Run locally without Docker

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # fill in OPENAI_API_KEY
uvicorn app.main:app --reload
```

In another terminal, serve the frontend (any static server works):

```bash
cd frontend
python -m http.server 5500
```

Open http://localhost:5500.

## API overview

| Method | Endpoint                    | Auth | Description                        |
|--------|------------------------------|------|-------------------------------------|
| POST   | `/auth/register`             | No   | Create a user account               |
| POST   | `/auth/login`                | No   | OAuth2 password flow → JWT          |
| POST   | `/upload`                    | Yes  | Upload + ingest a PDF/TXT/MD file   |
| POST   | `/chat`                      | Yes  | Ask a question, get a grounded answer |
| GET    | `/chat/history/{session_id}` | Yes  | Fetch a session's message history   |
| GET    | `/health`                    | No   | Liveness check                      |

Interactive Swagger docs are auto-generated at `/docs`.

## Notes & extension points

- **Embeddings run locally** (no API key needed) via sentence-transformers, so
  ingestion works even without an LLM key — only `/chat` requires `OPENAI_API_KEY`.
- **Multi-tenancy**: every chunk and chat message is tagged with `owner_id`,
  so users only ever retrieve their own documents.
- **Swap the vector store**: everything Chroma-specific lives in
  `services/vector_store.py` — replace it with Pinecone/PGVector/Weaviate by
  keeping the same `add_chunks` / `query` interface.
- **Swap the LLM provider**: `services/llm.py` isolates the provider call;
  point it at Anthropic, a local model, etc. by changing that one file.
- **Production checklist**: set a strong `SECRET_KEY`, move off SQLite to
  Postgres, put the frontend behind a real web server/CDN, add rate limiting,
  and restrict `CORS_ORIGINS`.

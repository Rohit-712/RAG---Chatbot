RAG Chatbot - AI Document Assistant

A full-stack Retrieval-Augmented Generation (RAG) chatbot that allows users to upload documents and ask questions about their content using semantic search and a Large Language Model.

==================================================
FEATURES
==================================================

• User registration and login
• JWT authentication
• PDF, TXT and Markdown document upload
• Automatic text extraction
• Text chunking with overlap
• Sentence Transformer embeddings
• FAISS vector similarity search
• Ollama local LLM integration
• Multi-document question answering
• Source-aware answers
• Source document, page, chunk and score information
• Chat history
• Document listing
• Document deletion
• User-specific document access
• SQLite + SQLAlchemy database
• Modern HTML/CSS/JavaScript frontend
• Docker configuration


==================================================
ARCHITECTURE
==================================================

                         RAG CHATBOT
                              |
                              v
                   +---------------------+
                   |      Frontend       |
                   |    HTML / CSS / JS  |
                   +----------+----------+
                              |
                           REST API
                              |
                              v
                   +---------------------+
                   |       FastAPI       |
                   |       Backend       |
                   +----------+----------+
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
        +-----------+   +-----------+   +-----------+
        |  SQLite   |   |   FAISS   |   |  Ollama   |
        | SQLAlchemy|   |  Vector   |   |    LLM    |
        +-----------+   +-----+-----+   +-----------+
                              |
                              v
                    +-------------------+
                    | Sentence          |
                    | Transformers      |
                    | Embeddings        |
                    +-------------------+


==================================================
RAG PIPELINE
==================================================

DOCUMENT INGESTION

Upload Document
      |
      v
Extract Text
      |
      v
Split Text into Chunks
      |
      v
Generate Embeddings
      |
      v
Store Embeddings in FAISS
      |
      v
Store Metadata in SQLite


QUESTION ANSWERING

User Question
      |
      v
Generate Query Embedding
      |
      v
FAISS Similarity Search
      |
      v
Retrieve Relevant Chunks
      |
      v
Build Context
      |
      v
Send Context + Question to Ollama
      |
      v
Generate Answer
      |
      v
Return Answer + Sources
      |
      v
Save Chat History


==================================================
TECH STACK
==================================================

BACKEND

• Python
• FastAPI
• Uvicorn
• SQLAlchemy
• SQLite
• JWT
• Pydantic

AI / RAG

• Sentence Transformers
• all-MiniLM-L6-v2
• FAISS
• Ollama
• llama3.2:3b

FRONTEND

• HTML5
• CSS3
• JavaScript
• Fetch API

DEPLOYMENT

• Docker
• Docker Compose
• AWS EC2 (Planned)


==================================================
PROJECT STRUCTURE
==================================================

RAG---Chatbot/
|
+-- backend/
|   |
|   +-- app/
|   |   |
|   |   +-- db/
|   |   +-- models/
|   |   +-- routes/
|   |   +-- services/
|   |   +-- utils/
|   |   +-- config.py
|   |   +-- main.py
|   |
|   +-- requirements.txt
|   +-- Dockerfile
|   +-- .env
|
+-- frontend/
|   |
|   +-- index.html
|   +-- style.css
|   +-- script.js
|
+-- .dockerignore
+-- .env.example
+-- .gitignore
+-- docker-compose.yml
+-- README.md


==================================================
REQUIREMENTS
==================================================

• Python 3.11+
• Git
• Ollama
• Modern web browser
• Docker Desktop for Docker testing


==================================================
INSTALLATION
==================================================

1. CLONE REPOSITORY

git clone https://github.com/Rohit-712/RAG---Chatbot.git

cd RAG---Chatbot


2. CREATE VIRTUAL ENVIRONMENT

WINDOWS

python -m venv venv

venv\Scripts\activate


LINUX / MACOS

python3 -m venv venv

source venv/bin/activate


3. INSTALL DEPENDENCIES

cd backend

pip install -r requirements.txt


==================================================
ENVIRONMENT CONFIGURATION
==================================================

Create the following file:

backend/.env

Example configuration:

DATABASE_URL=sqlite:///./data/app.db

SECRET_KEY=change-this-to-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

CHUNK_SIZE=800
CHUNK_OVERLAP=120
TOP_K=4

EMBEDDING_MODEL=all-MiniLM-L6-v2

FAISS_STORAGE_DIR=./data/faiss

UPLOAD_DIR=./uploads

MAX_UPLOAD_MB=25

OLLAMA_HOST=http://localhost:11434

LLM_MODEL=llama3.2:3b

LLM_TEMPERATURE=0.3

CORS_ORIGINS=["http://localhost:5500","http://127.0.0.1:5500","http://localhost:3000"]

GOOGLE_API_KEY=your_google_api_key_here

GEMINI_OCR_MODEL=gemini-3.5-flash


IMPORTANT:

Never upload your real .env file or API keys to GitHub.


==================================================
OLLAMA SETUP
==================================================

Check Ollama:

ollama list

Pull the required model:

ollama pull llama3.2:3b

Verify:

ollama list


==================================================
RUN BACKEND
==================================================

From the backend directory:

python -m uvicorn app.main:app --reload

Backend:

http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000/docs


==================================================
RUN FRONTEND
==================================================

Open the frontend folder in VS Code.

Run index.html using Live Server.

Example:

http://127.0.0.1:5500


==================================================
API ENDPOINTS
==================================================

AUTHENTICATION

POST /auth/register

POST /auth/login


DOCUMENTS

GET /documents

POST /upload

DELETE /documents/{document_id}


CHAT

POST /chat


==================================================
AUTHENTICATION FLOW
==================================================

User
  |
  v
Login
  |
  v
FastAPI
  |
  v
JWT Token
  |
  v
Frontend
  |
  v
Authorization: Bearer <token>
  |
  v
Protected API Endpoints


==================================================
EMBEDDINGS AND RETRIEVAL
==================================================

Embedding Model:

sentence-transformers/all-MiniLM-L6-v2


DOCUMENT PROCESSING

Document Chunk
      |
      v
Sentence Transformer
      |
      v
Embedding Vector
      |
      v
FAISS


QUERY PROCESSING

Question
   |
   v
Query Embedding
   |
   v
FAISS Search
   |
   v
Relevant Chunks


Default TOP_K:

TOP_K=4


==================================================
SOURCE INFORMATION
==================================================

The chatbot returns source information for retrieved content.

Example:

📄 Introduction_to_Network_Security_Case_Study.pdf
· Page 1
· Chunk 74
· Score 0.7259

This helps users understand which document content was retrieved for generating the answer.


==================================================
DOCUMENT MANAGEMENT
==================================================

Users can:

Upload Document
       |
       v
View Document
       |
       v
Ask Questions
       |
       v
Delete Document


Example delete response:

{
    "message": "Document deleted successfully.",
    "document_id": 2,
    "document_name": "example.pdf",
    "chunks_deleted": 10
}


==================================================
CHAT HISTORY
==================================================

The application stores:

• User questions
• Assistant responses
• Session ID
• User ID
• Creation timestamp


==================================================
DOCKER
==================================================

Build:

docker compose build

Run:

docker compose up

Stop:

docker compose down


Backend:

http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000/docs


The current Docker configuration is intended for development/testing.

Ollama networking may require configuration changes depending on where Ollama is running.


==================================================
SECURITY
==================================================

Never upload the following to GitHub:

• .env
• API keys
• Passwords
• JWT secret keys
• venv/
• Database files
• Uploaded documents
• Generated FAISS data

The project uses .gitignore to prevent sensitive and generated files from being committed.


==================================================
TROUBLESHOOTING
==================================================

401 UNAUTHORIZED

Make sure the request contains:

Authorization: Bearer <access_token>


For Swagger:

1. Login.
2. Copy the access token.
3. Click Authorize.
4. Enter the token.
5. Retry the protected endpoint.


409 DOCUMENT ALREADY EXISTS

The document already exists for the current user.

Delete the existing document or upload a differently named document.


OLLAMA CONNECTION ERROR

Check:

ollama list

Make sure:

LLM_MODEL=llama3.2:3b


FAISS ERROR

Check that the FAISS storage directory exists and that the application has permission to read and write the files.


==================================================
FUTURE IMPROVEMENTS
==================================================

• Streaming LLM responses
• Better page-aware PDF extraction
• Hybrid keyword + vector search
• Retrieval reranking
• Document preview
• Drag-and-drop uploads
• Chat history sidebar
• Background document processing
• PostgreSQL production database
• Cloud object storage
• Production Docker deployment
• AWS EC2 deployment
• CI/CD pipeline
• HTTPS
• Rate limiting
• Production logging
• Monitoring


==================================================
PLANNED AWS DEPLOYMENT
==================================================

GitHub
   |
   v
AWS EC2
   |
   v
Docker
   |
   v
FastAPI RAG Backend
   |
   v
FAISS + Sentence Transformers
   |
   v
Ollama
   |
   v
LLM


==================================================
PROJECT STATUS
==================================================

• User Registration - Complete
• User Login - Complete
• JWT Authentication - Complete
• Document Upload - Complete
• PDF Processing - Complete
• TXT Processing - Complete
• Markdown Processing - Complete
• Text Chunking - Complete
• Embeddings - Complete
• FAISS Retrieval - Complete
• Ollama LLM - Complete
• RAG Question Answering - Complete
• Source Display - Complete
• Chat History - Complete
• Document Listing - Complete
• Document Deletion - Complete
• Modern UI - Complete
• Docker Configuration - Complete
• GitHub Repository - Complete
• AWS Deployment - Planned


==================================================
AUTHOR
==================================================

Rohit Pawar

Python | AI/ML | Generative AI Developer

GitHub:
https://github.com/Rohit-712


==================================================
LICENSE
==================================================

This project is developed for educational, portfolio, and learning purposes.
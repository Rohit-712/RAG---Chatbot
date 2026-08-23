"""
Application entrypoint. Wires up middleware, routers, and startup hooks.

Run locally:
    uvicorn app.main:app --reload

Run via Docker:
    docker compose up --build
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import init_db
from app.routes import auth, upload, chat, documents
from app.routes.documents import router as documents_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(documents_router)


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}

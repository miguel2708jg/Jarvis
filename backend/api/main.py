"""FastAPI application - Jarvis backend."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.auth import auth_middleware
from backend.api.routers import calendar, chat, email, knowledge, notes, todos
from backend.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-warm the graph on startup
    from backend.api.dependencies import get_jarvis_graph

    get_jarvis_graph()
    yield


app = FastAPI(
    title="Jarvis API",
    version="1.0.0",
    description="Personal AI assistant powered by LangGraph + Ollama",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(auth_middleware)

app.include_router(chat.router, tags=["chat"])
app.include_router(notes.router, prefix="/notes", tags=["notes"])
app.include_router(todos.router, prefix="/todos", tags=["todos"])
app.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
app.include_router(email.router, prefix="/emails", tags=["email"])
app.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "jarvis"}

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.db.database import init_db
from app.api.routes_chat import router as chat_router
from app.api.routes_tasks import router as tasks_router
from app.api.routes_tools import router as tools_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing SQLite database tables...")
    init_db()
    logger.info(f"Multi-Tool AI Agent Backend ready on {settings.APP_HOST}:{settings.APP_PORT}")
    yield
    # Shutdown actions
    logger.info("Multi-Tool AI Agent Backend shutting down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production-ready backend for the Multi-Tool AI Agent – Intelligent Task Assistant. "
        "Powered by LangGraph, FastAPI, SQLite, and Pydantic."
    ),
    lifespan=lifespan
)

# Enable CORS for local Streamlit frontend and cross-origin clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(chat_router)
app.include_router(tasks_router)
app.include_router(tools_router)

@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "default_provider": settings.LLM_PROVIDER,
        "default_model": settings.DEFAULT_MODEL
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)

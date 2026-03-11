import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from authentication.auth_routes import router as auth_router
from config.database import init_database
from config.settings import settings

# Add AI-backend to path for session database initialization
_ai_backend_path = Path(__file__).parent.parent / "AI-backend"
if str(_ai_backend_path) not in sys.path:
    sys.path.insert(0, str(_ai_backend_path))
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from routes import session, user
from routes.chat import chat_router
from routes.health import health_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    Initializes database on startup.
    """
    # Startup
    print("=" * 80)
    print("NALA HEALTH COACH API - STARTING UP")
    print("=" * 80)

    # Initialize conversation database (SQLAlchemy models)
    print(f"\n🗄️  Initializing database: {settings.conversation_database_url}")
    try:
        init_database(settings.conversation_database_url)
        print("✓ Conversation database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        print("⚠️  API will start but database operations will fail")

    # Initialize AI-backend sessions table (raw psycopg2)
    try:
        from utils.database import init_database as init_sessions_db

        init_sessions_db()
        print("✓ Sessions table initialized successfully")
    except Exception as e:
        print(f"✗ Sessions table initialization failed: {e}")
        print("⚠️  Session save/load will fall back to file storage")

    print("\n" + "=" * 80)
    print("API READY")
    print("=" * 80)
    print(f"📍 API URL: http://{settings.api_host}:{settings.api_port}")
    print(f"📚 Docs: http://{settings.api_host}:{settings.api_port}/docs")
    print(f"🤖 AI Model: {settings.default_llm_model}")
    print(f"🔍 RAG Top-K: {settings.top_k_sources}")
    print("=" * 80 + "\n")

    yield  # API runs here

    # Shutdown
    print("\n🛑 Shutting down...")


app = FastAPI(
    title="Nala Health Coach API",
    description="Backend API for health coaching chatbot with RAG (Retrieval-Augmented Generation)",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,  # Allow both /health and /health/ to work
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS for React Native development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1/user")
app.include_router(session.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "Nala Health Coach API is running",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "chat": "/api/v1/chat/message",
            "stream": "/api/v1/chat/stream",
            "health": "/api/v1/health",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "app:app", host=settings.api_host, port=settings.api_port, reload=settings.debug
    )

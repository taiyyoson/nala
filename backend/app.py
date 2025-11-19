from contextlib import asynccontextmanager

import uvicorn
from config.database import init_database
from config.settings import settings
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from routes.chat import chat_router
from routes.health import health_router
from routes import user
from routes import session

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

    # Initialize database
    print(f"\n🗄️  Initializing database: {settings.conv_db_url}")
    try:
        init_database(settings.conv_db_url)
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        print("⚠️  API will start but database operations will fail")

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
)

# Configure CORS for React Native development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
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

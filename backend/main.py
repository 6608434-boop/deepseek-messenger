"""Main FastAPI application entry point.

This module initializes:
- FastAPI app with CORS
- API routes
- Startup and shutdown events
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.api import routes
from backend.core.dependencies import close_connections
from backend.core.dependencies import get_db, get_deepseek_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up DeepSeek Messenger API")

    # Initialize database and check connections
    try:
        db = await get_db()
        await db.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # Check DeepSeek API connection
    try:
        deepseek = await get_deepseek_client()
        health = await deepseek.health_check()
        if health:
            logger.info("DeepSeek API connection successful")
        else:
            logger.warning("DeepSeek API health check failed")
    except Exception as e:
        logger.error(f"Failed to connect to DeepSeek API: {e}")

    yield

    # Shutdown
    logger.info("Shutting down DeepSeek Messenger API")
    await close_connections()


# Create FastAPI app
app = FastAPI(
    title="DeepSeek Messenger API",
    description="Minimalist web messenger with DeepSeek integration",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "https://rare-renewal-production.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(routes.router)


@app.get("/")
async def root():
    """Root endpoint - redirect to docs."""
    return {
        "message": "DeepSeek Messenger API",
        "docs": "/docs",
        "version": "1.0.0"
    }


# For running directly with python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
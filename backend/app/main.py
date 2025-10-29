"""FastAPI application for Spotify Music Recommendation System"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api import recommendations, spotify_auth, health, recommendations_async, spotify_queue, streaming_recommendations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Gemini Model: {settings.gemini_model}")
    logger.info(f"Spotify OAuth URI: {settings.spotify_redirect_uri}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered music recommendation system with Spotify integration",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=settings.api_v1_prefix, tags=["health"])
app.include_router(recommendations.router, prefix=settings.api_v1_prefix, tags=["recommendations"])
app.include_router(recommendations_async.router, prefix=settings.api_v1_prefix, tags=["recommendations-async"])
app.include_router(streaming_recommendations.router, prefix=settings.api_v1_prefix, tags=["streaming"])
app.include_router(spotify_auth.router, prefix=settings.api_v1_prefix, tags=["spotify-auth"])
app.include_router(spotify_queue.router, prefix=f"{settings.api_v1_prefix}/spotify", tags=["spotify-queue"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "api": settings.api_v1_prefix
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


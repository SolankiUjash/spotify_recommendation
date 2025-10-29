"""Health check endpoints"""

from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.core.config import settings
import google.generativeai as genai

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services = {
        "gemini_configured": bool(settings.google_api_key),
        "spotify_configured": bool(settings.spotify_client_id and settings.spotify_client_secret),
    }
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        services=services
    )



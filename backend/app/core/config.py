"""Application configuration"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


def _parse_cors_origins(defaults: list[str]) -> list[str]:
    env_val = os.getenv("CORS_ORIGINS", "").strip()
    if not env_val:
        # Optionally add tunnel domain from env
        tunnel = os.getenv("TUNNEL_DOMAIN", "").strip()
        if tunnel:
            if tunnel.startswith("http"):
                defaults.append(tunnel)
            else:
                defaults.append(f"https://{tunnel}")
        return defaults
    parts = [p.strip() for p in env_val.split(",") if p.strip()]
    return parts or defaults


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    app_name: str = "Spotify Music Recommendation System"
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    
    # CORS Settings
    cors_origins: list[str] = _parse_cors_origins([
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://spotify.ujash.live",
    ])
    
    # Google Gemini API
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    # Spotify API
    spotify_client_id: str = os.getenv("SPOTIPY_CLIENT_ID", "")
    spotify_client_secret: str = os.getenv("SPOTIPY_CLIENT_SECRET", "")
    spotify_redirect_uri: str = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
    
    # Frontend base URL for post-auth redirects (use tunnel domain in prod)
    frontend_base_url: Optional[str] = os.getenv("FRONTEND_BASE_URL", None)
    
    # Redis (for session management - optional)
    redis_url: Optional[str] = os.getenv("REDIS_URL", None)
    
    # Session
    session_secret_key: str = os.getenv("SESSION_SECRET_KEY", "your-secret-key-change-this")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


"""Spotify authentication endpoints"""

import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import SpotifyAuthResponse
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/spotify/auth-url", response_model=SpotifyAuthResponse)
async def get_spotify_auth_url():
    """
    Get Spotify OAuth authorization URL
    
    Returns the URL that the frontend should redirect to for user authentication
    """
    try:
        from spotipy.oauth2 import SpotifyOAuth
        
        oauth = SpotifyOAuth(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            redirect_uri=settings.spotify_redirect_uri,
            scope="user-modify-playback-state user-read-playback-state user-read-currently-playing",
            show_dialog=False
        )
        
        auth_url = oauth.get_authorize_url()
        
        return SpotifyAuthResponse(
            auth_url=auth_url,
            message="Redirect user to this URL for Spotify authentication"
        )
        
    except Exception as exc:
        logger.error(f"Error generating auth URL: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/spotify/callback")
async def spotify_callback(code: str):
    """
    Handle Spotify OAuth callback
    
    Exchanges authorization code for access token
    """
    try:
        from spotipy.oauth2 import SpotifyOAuth
        
        oauth = SpotifyOAuth(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            redirect_uri=settings.spotify_redirect_uri,
            scope="user-modify-playback-state user-read-playback-state user-read-currently-playing"
        )
        
        token_info = oauth.get_access_token(code, as_dict=True, check_cache=False)
        
        if not token_info:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        return {
            "access_token": token_info["access_token"],
            "token_type": token_info["token_type"],
            "expires_in": token_info["expires_in"],
            "refresh_token": token_info.get("refresh_token"),
            "scope": token_info.get("scope")
        }
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in OAuth callback: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))



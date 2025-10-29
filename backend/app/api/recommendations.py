"""Recommendations API endpoints"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.models.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    SpotifyTrack,
    ErrorResponse
)
from app.core.config import settings

# Import the core classes from the CLI version
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from main import GeminiAgent, VerifierAgent, SpotifyClient, parse_title_and_artists_from_freeform

logger = logging.getLogger(__name__)
router = APIRouter()

# Global instances (in production, use dependency injection)
_gemini_agent = None
_verifier_agent = None


def get_gemini_agent() -> GeminiAgent:
    """Get or create Gemini agent"""
    global _gemini_agent
    if _gemini_agent is None:
        _gemini_agent = GeminiAgent(settings.google_api_key, settings.gemini_model)
    return _gemini_agent


def get_verifier_agent() -> VerifierAgent:
    """Get or create Verifier agent"""
    global _verifier_agent
    if _verifier_agent is None:
        _verifier_agent = VerifierAgent(settings.google_api_key, settings.gemini_model)
    return _verifier_agent


def get_spotify_client(access_token: Optional[str] = None) -> SpotifyClient:
    """Get Spotify client"""
    # For web app, we'll need to handle per-user tokens
    # For now, using app credentials
    return SpotifyClient(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_redirect_uri
    )


@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Get song recommendations based on a seed song
    
    - Resolves the seed song on Spotify
    - Gets AI-powered recommendations from Gemini
    - Optionally verifies recommendations
    - Returns matched tracks from Spotify
    """
    try:
        logger.info(f"Getting recommendations for: {request.seed_song}")
        
        # Initialize clients
        gemini = get_gemini_agent()
        verifier = get_verifier_agent() if request.verify else None
        spotify = get_spotify_client()
        
        # Resolve seed track
        seed_track_data = spotify.resolve_track(request.seed_song)
        if not seed_track_data:
            raise HTTPException(status_code=404, detail=f"Could not find '{request.seed_song}' on Spotify")
        
        # Extract seed track info
        seed_track_name = seed_track_data["name"]
        seed_artists = ", ".join(artist["name"] for artist in seed_track_data["artists"])
        seed_genre = None
        if "album" in seed_track_data and "genres" in seed_track_data.get("album", {}):
            genres = seed_track_data["album"].get("genres", [])
            if genres:
                seed_genre = ", ".join(genres[:2])
        
        # Get recommendations from Gemini
        suggestions = gemini.suggest(
            seed_song=seed_track_name,
            count=request.count,
            seed_artist=seed_artists,
            seed_genre=seed_genre
        )
        
        logger.info(f"Received {len(suggestions)} suggestions from Gemini")
        
        # Resolve and verify recommendations
        recommendations = []
        verified_count = 0
        rejected_count = 0
        
        for suggestion in suggestions:
            # Resolve on Spotify
            track = spotify.resolve_track(suggestion.title, suggestion.artists)
            if not track:
                logger.warning(f"Could not find on Spotify: {suggestion.title}")
                continue
            
            # Verify if enabled
            verification = None
            if verifier:
                verification = verifier.verify_recommendation(
                    seed_song=seed_track_name,
                    seed_artist=seed_artists,
                    seed_genre=seed_genre,
                    recommended_song=suggestion,
                    recommended_track=track
                )
                
                if not verification.is_valid:
                    rejected_count += 1
                    logger.info(f"Rejected: {track['name']} - {verification.reason}")
                    continue
                    
                verified_count += 1
            
            # Build recommendation object
            rec_artists = [artist["name"] for artist in track.get("artists", [])]
            album_images = track.get("album", {}).get("images", [])
            image_url = album_images[0]["url"] if album_images else None
            
            recommendations.append({
                "suggestion": {
                    "title": suggestion.title,
                    "artists": suggestion.artists,
                    "genre": suggestion.genre,
                    "reason": suggestion.reason
                },
                "track": {
                    "id": track["id"],
                    "name": track["name"],
                    "artists": rec_artists,
                    "album": track.get("album", {}).get("name", ""),
                    "uri": track["uri"],
                    "popularity": track.get("popularity", 0),
                    "preview_url": track.get("preview_url"),
                    "image_url": image_url
                },
                "verification": {
                    "is_valid": verification.is_valid if verification else True,
                    "confidence_score": verification.confidence_score if verification else 1.0,
                    "reason": verification.reason if verification else "Not verified"
                } if verification else None
            })
        
        # Build seed track response
        seed_album_images = seed_track_data.get("album", {}).get("images", [])
        seed_image_url = seed_album_images[0]["url"] if seed_album_images else None
        seed_track = SpotifyTrack(
            id=seed_track_data["id"],
            name=seed_track_data["name"],
            artists=[a["name"] for a in seed_track_data["artists"]],
            album=seed_track_data.get("album", {}).get("name", ""),
            uri=seed_track_data["uri"],
            popularity=seed_track_data.get("popularity", 0),
            preview_url=seed_track_data.get("preview_url"),
            image_url=seed_image_url
        )
        
        return RecommendationResponse(
            seed_track=seed_track,
            recommendations=recommendations,
            total_found=len(recommendations),
            total_verified=verified_count if verifier else len(recommendations),
            total_rejected=rejected_count
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error getting recommendations: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))



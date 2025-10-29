"""Async Recommendations API endpoints with streaming support"""

import logging
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional
import asyncio

from app.models.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    SpotifyTrack,
)
from app.core.config import settings
from app.agents.gemini_agent_async import GeminiAgentAsync
from app.agents.verifier_agent_async import VerifierAgentAsync
from app.services.spotify_async import SpotifyClientAsync
import spotipy
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger(__name__)
router = APIRouter()

# Global instances
_gemini_agent = None
_verifier_agent = None


def get_gemini_agent() -> GeminiAgentAsync:
    """Get or create async Gemini agent"""
    global _gemini_agent
    if _gemini_agent is None:
        _gemini_agent = GeminiAgentAsync(settings.google_api_key, settings.gemini_model)
    return _gemini_agent


def get_verifier_agent() -> VerifierAgentAsync:
    """Get or create async Verifier agent"""
    global _verifier_agent
    if _verifier_agent is None:
        _verifier_agent = VerifierAgentAsync(settings.google_api_key, settings.gemini_model)
    return _verifier_agent


def get_spotify_client(access_token: Optional[str] = None) -> SpotifyClientAsync:
    """Get async Spotify client"""
    return SpotifyClientAsync(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_redirect_uri
    )


def get_spotify_sync_client():
    """Get sync Spotify client for queue operations"""
    oauth = SpotifyOAuth(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_redirect_uri,
        scope="user-modify-playback-state user-read-playback-state",
        cache_path=".cache-spotify",
        open_browser=False,
    )
    return spotipy.Spotify(auth_manager=oauth)


@router.post("/recommendations-async", response_model=RecommendationResponse)
async def get_recommendations_async(request: RecommendationRequest):
    """
    Get song recommendations (fully async version)
    
    - Resolves the seed song on Spotify
    - Gets AI-powered recommendations from Gemini
    - Batch verifies recommendations (single LLM call)
    - Auto-adds accepted tracks to Spotify queue
    - Returns matched tracks from Spotify
    
    All operations run concurrently for maximum speed.
    """
    try:
        logger.info(f"[ASYNC] Getting recommendations for: {request.seed_song}")
        
        # Initialize clients
        gemini = get_gemini_agent()
        verifier = get_verifier_agent() if request.verify else None
        spotify = get_spotify_client()
        
        # Step 1: Resolve seed track
        seed_track_data = await spotify.resolve_track(request.seed_song)
        if not seed_track_data:
            raise HTTPException(status_code=404, detail=f"Could not find '{request.seed_song}' on Spotify")
        
        # Extract seed info
        seed_track_name = seed_track_data["name"]
        seed_artists = ", ".join(artist["name"] for artist in seed_track_data["artists"])
        seed_genre = None
        if "album" in seed_track_data and "genres" in seed_track_data.get("album", {}):
            genres = seed_track_data["album"].get("genres", [])
            if genres:
                seed_genre = ", ".join(genres[:2])
        
        # Step 2: Get recommendations from Gemini (async)
        suggestions = await gemini.suggest(
            seed_song=seed_track_name,
            count=request.count,
            seed_artist=seed_artists,
            seed_genre=seed_genre
        )
        
        logger.info(f"[ASYNC] Received {len(suggestions)} suggestions from Gemini")
        
        # Step 3: Resolve all suggestions on Spotify first
        resolved_tracks = []
        for suggestion in suggestions:
            track = await spotify.resolve_track(suggestion.title, suggestion.artists)
            if track:
                resolved_tracks.append((suggestion, track))
            else:
                logger.warning(f"Could not find on Spotify: {suggestion.title}")
        
        # Step 4: Batch verification if enabled (single API call)
        verification_results = []
        if verifier and resolved_tracks:
            logger.info(f"[ASYNC] Running batch verification for {len(resolved_tracks)} tracks")
            verification_results = await verifier.verify_batch(
                seed_track_name,
                seed_artists,
                seed_genre,
                resolved_tracks
            )
        
        # Step 5: Ensure active device and build recommendations
        spotify_sync = get_spotify_sync_client()
        
        # Check for active device and try to activate one
        try:
            devices = spotify_sync.devices()
            active_device = None
            for device in devices.get("devices", []):
                if device.get("is_active"):
                    active_device = device
                    break
            
            if not active_device and devices.get("devices"):
                # Try to activate the first available device
                first_device = devices["devices"][0]
                device_id = first_device["id"]
                logger.info(f"No active device found. Attempting to activate: {first_device['name']}")
                try:
                    spotify_sync.start_playback(device_id=device_id)
                    active_device = first_device
                    logger.info(f"Successfully activated device: {first_device['name']}")
                except Exception as device_exc:
                    logger.warning(f"Failed to activate device: {device_exc}")
            
            if not active_device:
                logger.warning("No active Spotify device found. Songs will not be added to queue.")
        except Exception as device_exc:
            logger.warning(f"Failed to check/activate devices: {device_exc}")
        
        recommendations = []
        rejected_count = 0
        added_to_queue_count = 0
        
        for idx, (suggestion, track) in enumerate(resolved_tracks):
            verification = verification_results[idx] if idx < len(verification_results) else None
            
            # Check verification if enabled
            if verification and not verification.is_valid:
                logger.info(f"Rejected: {track['name']} - {verification.reason}")
                rejected_count += 1
                continue
            
            # Auto-add to Spotify queue
            in_queue = False
            try:
                spotify_sync.add_to_queue(track["uri"])
                added_to_queue_count += 1
                in_queue = True
                logger.info(f"Added to queue: {track['name']}")
            except Exception as queue_exc:
                logger.warning(f"Failed to add to queue: {queue_exc}")
            
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
                } if verification else None,
                "in_queue": in_queue
            })
        
        verified_count = len(recommendations)
        logger.info(f"[ASYNC] Added {added_to_queue_count} tracks to Spotify queue")
        
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


@router.websocket("/recommendations/stream")
async def stream_recommendations(websocket: WebSocket):
    """
    WebSocket endpoint for streaming recommendations in real-time
    
    Client sends: {"seed_song": "...", "count": 5, "verify": true}
    Server streams: {
        "type": "status|chunk|track|complete|error",
        "data": {...}
    }
    """
    await websocket.accept()
    
    try:
        # Receive request
        data = await websocket.receive_json()
        seed_song = data.get("seed_song")
        count = data.get("count", 5)
        verify = data.get("verify", True)
        
        if not seed_song:
            await websocket.send_json({"type": "error", "error": "seed_song is required"})
            await websocket.close()
            return
        
        logger.info(f"[STREAM] Processing: {seed_song}")
        
        # Initialize clients
        gemini = get_gemini_agent()
        verifier = get_verifier_agent() if verify else None
        spotify = get_spotify_client()
        
        # Step 1: Resolve seed
        await websocket.send_json({"type": "status", "message": "Searching for seed song on Spotify..."})
        seed_track_data = await spotify.resolve_track(seed_song)
        
        if not seed_track_data:
            await websocket.send_json({"type": "error", "error": f"Could not find '{seed_song}' on Spotify"})
            await websocket.close()
            return
        
        seed_track_name = seed_track_data["name"]
        seed_artists = ", ".join(artist["name"] for artist in seed_track_data["artists"])
        seed_genre = None
        if "album" in seed_track_data and "genres" in seed_track_data.get("album", {}):
            genres = seed_track_data["album"].get("genres", [])
            if genres:
                seed_genre = ", ".join(genres[:2])
        
        # Send seed track
        await websocket.send_json({
            "type": "seed",
            "data": {
                "name": seed_track_name,
                "artists": seed_artists,
                "genre": seed_genre
            }
        })
        
        # Step 2: Stream recommendations from Gemini
        async for chunk in gemini.suggest_stream(seed_track_name, count, seed_artists, seed_genre):
            if chunk["type"] == "complete":
                # Got all suggestions, now resolve them
                await websocket.send_json({"type": "status", "message": f"Got {chunk['count']} suggestions, resolving on Spotify..."})
                
                # Process each suggestion
                for idx, suggestion_dict in enumerate(chunk["suggestions"]):
                    from app.models.schemas import SongSuggestion
                    suggestion = SongSuggestion(**suggestion_dict)
                    
                    # Resolve
                    track = await spotify.resolve_track(suggestion.title, suggestion.artists)
                    if not track:
                        await websocket.send_json({
                            "type": "skip",
                            "data": {"title": suggestion.title, "reason": "Not found on Spotify"}
                        })
                        continue
                    
                    # Verify if needed
                    if verifier:
                        verification = await verifier.verify_recommendation(
                            seed_song=seed_track_name,
                            seed_artist=seed_artists,
                            seed_genre=seed_genre,
                            recommended_song=suggestion,
                            recommended_track=track
                        )
                        
                        if not verification.is_valid:
                            await websocket.send_json({
                                "type": "rejected",
                                "data": {
                                    "title": track["name"],
                                    "reason": verification.reason
                                }
                            })
                            continue
                    
                    # Send valid track
                    rec_artists = [artist["name"] for artist in track.get("artists", [])]
                    album_images = track.get("album", {}).get("images", [])
                    image_url = album_images[0]["url"] if album_images else None
                    
                    await websocket.send_json({
                        "type": "track",
                        "data": {
                            "id": track["id"],
                            "name": track["name"],
                            "artists": rec_artists,
                            "album": track.get("album", {}).get("name", ""),
                            "uri": track["uri"],
                            "popularity": track.get("popularity", 0),
                            "preview_url": track.get("preview_url"),
                            "image_url": image_url,
                            "genre": suggestion.genre,
                            "reason": suggestion.reason
                        }
                    })
            else:
                # Forward status/chunk updates
                await websocket.send_json(chunk)
        
        # Done
        await websocket.send_json({"type": "complete", "message": "All recommendations processed"})
        
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as exc:
        logger.error(f"WebSocket error: {exc}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "error": str(exc)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


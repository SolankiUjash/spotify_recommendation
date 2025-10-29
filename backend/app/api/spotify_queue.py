"""Spotify Queue API endpoints"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class AddToQueueRequest(BaseModel):
    """Request to add track to queue"""
    track_uri: str


class RemoveFromQueueRequest(BaseModel):
    """Request to remove track from queue"""
    track_uri: str


class QueueResponse(BaseModel):
    """Queue operation response"""
    success: bool
    message: str


def get_spotify_client():
    """Get Spotify client with OAuth"""
    oauth = SpotifyOAuth(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_redirect_uri,
        scope="user-modify-playback-state user-read-playback-state",
        cache_path=".cache-spotify",
        open_browser=False,
    )
    return spotipy.Spotify(auth_manager=oauth)


@router.post("/queue/add", response_model=QueueResponse)
async def add_to_queue(request: AddToQueueRequest):
    """
    Add a track to the Spotify queue
    
    - Requires an active Spotify device
    - Track will be added to the end of the queue
    """
    try:
        spotify = get_spotify_client()
        
        # Check for active device
        devices = spotify.devices()
        if not devices.get("devices"):
            raise HTTPException(
                status_code=400,
                detail="No Spotify devices found. Please open Spotify on a device first."
            )
        
        active_device = None
        for device in devices["devices"]:
            if device.get("is_active"):
                active_device = device
                break
        
        if not active_device:
            # Use first available device
            active_device = devices["devices"][0]
            logger.info(f"No active device, using: {active_device['name']}")
        
        # Add to queue
        spotify.add_to_queue(request.track_uri, device_id=active_device["id"])
        
        logger.info(f"Added {request.track_uri} to queue on {active_device['name']}")
        
        return QueueResponse(
            success=True,
            message=f"Track added to queue on {active_device['name']}"
        )
        
    except spotipy.exceptions.SpotifyException as exc:
        logger.error(f"Spotify API error: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error adding to queue: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/queue/remove", response_model=QueueResponse)
async def remove_from_queue(request: RemoveFromQueueRequest):
    """
    Remove a track from the Spotify queue
    
    Note: Spotify API doesn't support removing specific tracks from queue.
    This endpoint will skip to the next track if the requested track is currently playing.
    For queued tracks, they cannot be removed directly via the API.
    """
    try:
        spotify = get_spotify_client()
        
        # Get current playback
        playback = spotify.current_playback()
        
        if not playback or not playback.get("item"):
            return QueueResponse(
                success=False,
                message="No track is currently playing"
            )
        
        current_track_uri = playback["item"]["uri"]
        
        # If the requested track is currently playing, skip it
        if current_track_uri == request.track_uri:
            spotify.next_track()
            return QueueResponse(
                success=True,
                message="Skipped the currently playing track"
            )
        else:
            # Spotify doesn't support removing queued tracks
            # We can only inform the user
            return QueueResponse(
                success=False,
                message="Cannot remove queued tracks via Spotify API. You can skip them manually in Spotify."
            )
        
    except spotipy.exceptions.SpotifyException as exc:
        logger.error(f"Spotify API error: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error removing from queue: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/queue/current")
async def get_current_queue():
    """
    Get the current Spotify queue
    
    Note: This endpoint returns the current playback state.
    The Spotify API has limited queue visibility.
    """
    try:
        spotify = get_spotify_client()
        
        # Get current playback
        playback = spotify.current_playback()
        
        if not playback:
            return {
                "is_playing": False,
                "current_track": None,
                "device": None
            }
        
        current_track = None
        if playback.get("item"):
            current_track = {
                "uri": playback["item"]["uri"],
                "name": playback["item"]["name"],
                "artists": [artist["name"] for artist in playback["item"]["artists"]],
                "album": playback["item"]["album"]["name"]
            }
        
        return {
            "is_playing": playback.get("is_playing", False),
            "current_track": current_track,
            "device": {
                "name": playback["device"]["name"],
                "type": playback["device"]["type"],
                "volume": playback["device"]["volume_percent"]
            } if playback.get("device") else None
        }
        
    except spotipy.exceptions.SpotifyException as exc:
        logger.error(f"Spotify API error: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error getting queue: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))



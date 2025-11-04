"""Spotify Queue API endpoints"""

import logging
from fastapi import APIRouter, HTTPException, Request
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


def get_spotify_client_from_cookies(request: Request):
    """Create Spotipy client using per-user cookies (multi-user safe)."""
    access = request.cookies.get("spotify_access_token")
    refresh = request.cookies.get("spotify_refresh_token")
    if not access and refresh:
        try:
            oauth = SpotifyOAuth(
                client_id=settings.spotify_client_id,
                client_secret=settings.spotify_client_secret,
                redirect_uri=settings.spotify_redirect_uri,
                scope="user-modify-playback-state user-read-playback-state",
            )
            token_info = oauth.refresh_access_token(refresh)
            access = token_info.get("access_token")
        except Exception:
            access = None
    if not access:
        raise HTTPException(status_code=401, detail="Not authenticated with Spotify. Visit /api/v1/spotify/login")
    return spotipy.Spotify(auth=access)


@router.post("/queue/add", response_model=QueueResponse)
async def add_to_queue(request: AddToQueueRequest, http_request: Request):
    """
    Add a track to the Spotify queue
    
    - Requires an active Spotify device
    - Track will be added to the end of the queue
    """
    try:
        spotify = get_spotify_client_from_cookies(http_request)
        
        # Discover devices
        devices = spotify.devices()
        if not devices.get("devices"):
            raise HTTPException(
                status_code=400,
                detail="No Spotify devices found. Open Spotify on your phone/computer first."
            )

        # Prefer active device
        active_device = None
        for device in devices["devices"]:
            if device.get("is_active"):
                active_device = device
                break

        # If none active, try to activate the first available device
        if not active_device:
            candidate = devices["devices"][0]
            logger.info(f"No active device; attempting transfer to: {candidate['name']}")
            try:
                spotify.transfer_playback(device_id=candidate["id"], force_play=False)
                active_device = candidate
            except Exception as exc:
                logger.warning(f"Failed to transfer playback: {exc}")
                active_device = candidate  # still try queueing against it

        # Try adding to queue with device id first
        try:
            spotify.add_to_queue(request.track_uri, device_id=active_device["id"])
        except spotipy.exceptions.SpotifyException as exc:
            # Some mobile devices reject device_id with 404; retry without device_id
            logger.warning(f"Add to queue with device_id failed ({active_device['name']}), retrying without device: {exc}")
            try:
                spotify.add_to_queue(request.track_uri)
            except spotipy.exceptions.SpotifyException as exc2:
                logger.error(f"Spotify API error: {exc2}")
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Unable to add to queue. Ensure Spotify is open on your phone, "
                        "you have Premium, and play any song once to activate the device, then try again."
                    ),
                )
        
        logger.info(f"Added {request.track_uri} to queue on {active_device['name']}")
        
        return QueueResponse(
            success=True,
            message=f"Track added to queue on {active_device['name']}"
        )
        
    except spotipy.exceptions.SpotifyException as exc:
        logger.error(f"Spotify API error: {exc}")
        raise HTTPException(status_code=400, detail="Spotify error while adding to queue")
    except HTTPException:
        # Preserve upstream HTTP status (e.g., 401 when not authenticated)
        raise
    except Exception as exc:
        logger.error(f"Error adding to queue: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/queue/remove", response_model=QueueResponse)
async def remove_from_queue(request: RemoveFromQueueRequest, http_request: Request):
    """
    Remove a track from the Spotify queue.

    Strategy:
        1. If the track is currently playing → skip to the next track.
        2. If the track is further in the queue → rebuild the queue without it by calling
           `start_playback` with the remaining tracks (preserving current track & progress).

    Spotify does not expose a direct "remove" endpoint, so this is the safest workaround
    that keeps playback running with the updated queue.
    """
    try:
        spotify = get_spotify_client_from_cookies(http_request)

        # Get current playback (for device, current track, and progress)
        playback = spotify.current_playback()
        if not playback or not playback.get("device"):
            raise HTTPException(
                status_code=400,
                detail="No active Spotify device found. Start playback once in Spotify and try again."
            )

        device_id = playback["device"]["id"]
        current_track = playback.get("item")
        current_track_uri = current_track["uri"] if current_track else None
        progress_ms = playback.get("progress_ms", 0) if current_track_uri else 0

        # If the requested track is currently playing, simply skip it
        if current_track_uri and current_track_uri == request.track_uri:
            spotify.next_track()
            logger.info(f"Skipped currently playing track: {request.track_uri}")
            return QueueResponse(success=True, message="Skipped currently playing track")

        # Otherwise, rebuild the queue without the target track
        try:
            queue_data = spotify.queue()
        except spotipy.exceptions.SpotifyException as queue_exc:
            logger.error(f"Unable to access Spotify queue: {queue_exc}")
            raise HTTPException(
                status_code=400,
                detail="Your Spotify account cannot access the queue right now. Please try again later."
            )

        queue_tracks = queue_data.get("queue", [])
        if not queue_tracks:
            return QueueResponse(success=False, message="No upcoming tracks to modify")

        remaining_uris = []
        if current_track_uri:
            remaining_uris.append(current_track_uri)

        removed = False
        for track in queue_tracks:
            uri = track.get("uri")
            if not uri:
                continue
            if not removed and uri == request.track_uri:
                removed = True
                logger.info(f"Removing track from upcoming queue: {request.track_uri}")
                continue
            remaining_uris.append(uri)

        if not removed:
            return QueueResponse(success=False, message="Track not found in queue")

        # Restart playback with the updated queue
        # The first URI should stay the current track; provide progress to avoid jump
        spotify.start_playback(
            device_id=device_id,
            uris=remaining_uris,
            position_ms=progress_ms if current_track_uri else 0
        )

        return QueueResponse(success=True, message="Track removed from queue")

    except spotipy.exceptions.SpotifyException as exc:
        logger.error(f"Spotify API error: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error removing from queue: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/queue/current")
async def get_current_queue(http_request: Request):
    """
    Get the current Spotify queue
    
    Note: This endpoint returns the current playback state.
    The Spotify API has limited queue visibility.
    """
    try:
        spotify = get_spotify_client_from_cookies(http_request)
        
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
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error getting queue: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))



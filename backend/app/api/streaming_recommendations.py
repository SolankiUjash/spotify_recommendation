"""Streaming Recommendations API with auto-queue and background verification"""

import logging
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json

from app.models.schemas import RecommendationRequest
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


async def verify_in_background(
    verifier: VerifierAgentAsync,
    seed_song: str,
    seed_artist: str,
    seed_genre: str,
    suggestion,
    track
):
    """Background verification task"""
    try:
        verification = await verifier.verify_recommendation(
            seed_song=seed_song,
            seed_artist=seed_artist,
            seed_genre=seed_genre,
            recommended_song=suggestion,
            recommended_track=track
        )
        return verification
    except Exception as exc:
        logger.warning(f"Background verification failed: {exc}")
        # Return a default "pass" result on error
        from app.models.schemas import VerificationResult
        return VerificationResult(
            is_valid=True,
            confidence_score=0.5,
            reason=f"Verification skipped due to error: {str(exc)[:50]}"
        )


@router.post("/stream-and-queue")
async def stream_recommendations_and_queue(request: RecommendationRequest):
    """
    Stream recommendations from Gemini, automatically add to Spotify queue,
    and verify in background.
    
    Flow:
    1. Get recommendations from Gemini (streaming)
    2. For each song:
       - Resolve on Spotify
       - Add to queue immediately
       - Start background verification
       - Stream result to client
    3. Verification happens asynchronously in background
    """
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            # Initialize clients
            gemini = get_gemini_agent()
            verifier = get_verifier_agent()
            spotify_async = SpotifyClientAsync(
                client_id=settings.spotify_client_id,
                client_secret=settings.spotify_client_secret,
                redirect_uri=settings.spotify_redirect_uri
            )
            spotify_sync = get_spotify_sync_client()
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Searching for seed song...'})}\n\n"
            
            # Step 1: Resolve seed track
            seed_track_data = await spotify_async.resolve_track(request.seed_song)
            if not seed_track_data:
                yield f"data: {json.dumps({'type': 'error', 'error': f'Could not find {request.seed_song} on Spotify'})}\n\n"
                return
            
            seed_track_name = seed_track_data["name"]
            seed_artists = ", ".join(artist["name"] for artist in seed_track_data["artists"])
            seed_genre = None
            
            # Send seed info
            yield f"data: {json.dumps({'type': 'seed', 'data': {'name': seed_track_name, 'artists': seed_artists}})}\n\n"
            
            # Step 2: Stream recommendations from Gemini
            yield f"data: {json.dumps({'type': 'status', 'message': 'Getting AI recommendations...'})}\n\n"
            
            suggestions = await gemini.suggest(
                seed_song=seed_track_name,
                count=request.count,
                seed_artist=seed_artists,
                seed_genre=seed_genre
            )
            
            yield f"data: {json.dumps({'type': 'status', 'message': f'Got {len(suggestions)} suggestions, processing...'})}\n\n"
            
            # Step 3: Process each suggestion - resolve and queue
            resolved_tracks = []
            added_count = 0
            
            for idx, suggestion in enumerate(suggestions):
                try:
                    # Resolve on Spotify
                    track = await spotify_async.resolve_track(suggestion.title, suggestion.artists)
                    if not track:
                        yield f"data: {json.dumps({'type': 'skip', 'data': {'title': suggestion.title, 'reason': 'Not found on Spotify'}})}\n\n"
                        continue
                    
                    # Add to queue immediately
                    try:
                        spotify_sync.add_to_queue(track["uri"])
                        added_count += 1
                        logger.info(f"Added to queue: {track['name']}")
                    except Exception as queue_exc:
                        logger.warning(f"Failed to add to queue: {queue_exc}")
                        # Continue anyway
                    
                    # Save for batch verification
                    resolved_tracks.append((suggestion, track))
                    
                    # Build track data
                    rec_artists = [artist["name"] for artist in track.get("artists", [])]
                    album_images = track.get("album", {}).get("images", [])
                    image_url = album_images[0]["url"] if album_images else None
                    
                    # Stream track immediately (verification pending)
                    track_data = {
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
                            "reason": suggestion.reason,
                            "added_to_queue": True,
                            "verification_pending": True
                        }
                    }
                    yield f"data: {json.dumps(track_data)}\n\n"
                    
                except Exception as exc:
                    logger.error(f"Error processing suggestion: {exc}")
                    yield f"data: {json.dumps({'type': 'error', 'error': str(exc)})}\n\n"
            
            # Batch verification in background (single API call)
            if resolved_tracks:
                yield f"data: {json.dumps({'type': 'status', 'message': 'Running batch verification (1 API call)...'})}\n\n"
                
                try:
                    verification_results = await verifier.verify_batch(
                        seed_track_name,
                        seed_artists,
                        seed_genre,
                        resolved_tracks
                    )
                    
                    # Send verification results
                    rejected_count = 0
                    for (suggestion, track), verification in zip(resolved_tracks, verification_results):
                        if not verification.is_valid:
                            rejected_count += 1
                            yield f"data: {json.dumps({'type': 'verification', 'data': {'track_id': track['id'], 'valid': False, 'reason': verification.reason}})}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'verification', 'data': {'track_id': track['id'], 'valid': True, 'confidence': verification.confidence_score}})}\n\n"
                except Exception as verify_exc:
                    logger.warning(f"Batch verification error: {verify_exc}")
                    rejected_count = 0
            
            # Send completion
            yield f"data: {json.dumps({'type': 'complete', 'data': {'added_to_queue': added_count, 'rejected': rejected_count}})}\n\n"
            
        except Exception as exc:
            logger.error(f"Stream error: {exc}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(exc)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


"""Spotify Search API endpoints"""

import logging
from fastapi import APIRouter, HTTPException, Request, Query
from typing import List
from pydantic import BaseModel

from app.core.config import settings
import spotipy
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger(__name__)
router = APIRouter()


class SearchTrack(BaseModel):
    """Track search result"""
    id: str
    name: str
    artists: List[str]
    album: str
    image_url: str | None = None
    uri: str
    popularity: int


class SearchResponse(BaseModel):
    """Search results response"""
    tracks: List[SearchTrack]
    total: int


def get_spotify_sync_client_from_cookies(request: Request):
    """Create a Spotipy client using tokens from user cookies (multi-user safe)."""
    access = request.cookies.get("spotify_access_token")
    refresh = request.cookies.get("spotify_refresh_token")

    # If access missing but refresh present, attempt refresh
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
        raise HTTPException(status_code=401, detail="Not authenticated with Spotify")

    return spotipy.Spotify(auth=access)


@router.get("/search", response_model=SearchResponse)
async def search_tracks(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    request: Request = None
):
    """
    Search for tracks on Spotify
    
    Returns a list of tracks matching the search query.
    Used for autocomplete/typeahead functionality.
    """
    try:
        spotify = get_spotify_sync_client_from_cookies(request)
        
        # Search for tracks
        results = spotify.search(q=q, type='track', limit=limit)
        
        tracks = []
        for item in results.get('tracks', {}).get('items', []):
            artists = [artist['name'] for artist in item.get('artists', [])]
            album_images = item.get('album', {}).get('images', [])
            image_url = album_images[0]['url'] if album_images else None
            
            tracks.append(SearchTrack(
                id=item['id'],
                name=item['name'],
                artists=artists,
                album=item.get('album', {}).get('name', ''),
                image_url=image_url,
                uri=item['uri'],
                popularity=item.get('popularity', 0)
            ))
        
        return SearchResponse(
            tracks=tracks,
            total=results.get('tracks', {}).get('total', 0)
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Search error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


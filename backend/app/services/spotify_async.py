"""Async Spotify client wrapper"""

import logging
from typing import Optional, Dict, Any, List
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger(__name__)


# Import fuzzy matching from main.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from main import parse_title_and_artists_from_freeform, _score_track_match


class SpotifyClientAsync:
    """Async wrapper for Spotify client"""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        cache_path: str = ".cache-spotify",
    ) -> None:
        self.oauth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="user-modify-playback-state user-read-playback-state user-read-currently-playing",
            cache_path=cache_path,
            open_browser=False,
        )
        self.client = spotipy.Spotify(auth_manager=self.oauth)
        logger.info("Initialized Async Spotify client")

    async def resolve_track(
        self, 
        title: str, 
        artists: Optional[List[str]] = None,
        retries: int = 2
    ) -> Optional[Dict[str, Any]]:
        """Async track resolution with fuzzy matching"""
        
        def _resolve_sync():
            queries: List[str] = []
            
            parsed_title, parsed_artists = parse_title_and_artists_from_freeform(title)
            title_only = parsed_title
            artist_list = artists or parsed_artists
            
            if artist_list:
                for artist in artist_list:
                    queries.append(f'track:"{title_only}" artist:"{artist}"')
            queries.append(f'track:"{title_only}"')
            queries.append(title_only)
            
            best: Optional[Dict[str, Any]] = None
            best_score: float = 0.0
            
            for query in queries:
                for attempt in range(retries):
                    try:
                        result = self.client.search(q=query, type="track", limit=20)
                        tracks = result.get("tracks", {}).get("items", [])
                        for t in tracks:
                            score = _score_track_match(title_only, artist_list, t)
                            if score > best_score:
                                best = t
                                best_score = score
                        if best_score >= 0.75:
                            return best
                    except Exception as exc:
                        logger.warning(f"Search failed for '{query}': {exc}")
                        if attempt < retries - 1:
                            import time
                            time.sleep(0.5)
            
            if best and best_score >= 0.45:
                return best
            return None
        
        # Run blocking Spotify call in thread pool
        return await asyncio.to_thread(_resolve_sync)

    async def add_to_queue(self, track_uri: str) -> bool:
        """Async add to queue"""
        try:
            await asyncio.to_thread(self.client.add_to_queue, track_uri)
            return True
        except Exception as exc:
            logger.error(f"Failed to add track to queue: {exc}")
            return False

    async def start_playback(self, track_uri: str) -> bool:
        """Async start playback"""
        try:
            await asyncio.to_thread(self.client.start_playback, uris=[track_uri])
            return True
        except Exception as exc:
            logger.error(f"Failed to start playback: {exc}")
            return False

    async def get_active_device(self) -> Optional[Dict[str, Any]]:
        """Async get active device"""
        try:
            def _get_device():
                devices = self.client.devices().get("devices", [])
                for device in devices:
                    if device.get("is_active"):
                        return device
                return devices[0] if devices else None
            
            return await asyncio.to_thread(_get_device)
        except Exception as exc:
            logger.error(f"Failed to get devices: {exc}")
            return None



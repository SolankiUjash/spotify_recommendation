"""
Spotify Music Recommendation System
Uses Gemini AI to suggest similar songs and adds them to your Spotify queue.
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

import google.generativeai as genai
import spotipy
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from spotipy.oauth2 import SpotifyOAuth
from urllib.parse import urlparse, urlunparse
import re

# Load environment variables from .env file
load_dotenv()

# Configure logging with rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, show_time=False)]
)
logger = logging.getLogger(__name__)
console = Console()


class SongSuggestion(BaseModel):
    """Model for a song suggestion from Gemini"""
    title: str = Field(..., description="Song title")
    artists: List[str] = Field(..., description="List of artist names")
    genre: Optional[str] = Field(None, description="Music genre")
    reason: Optional[str] = Field(None, description="Reason for recommendation")


class SongRecommendations(BaseModel):
    """Model for the full recommendations response"""
    songs: List[SongSuggestion] = Field(..., description="List of recommended songs")


class VerificationResult(BaseModel):
    """Model for song verification result"""
    is_valid: bool = Field(..., description="Whether the song is a valid recommendation")
    confidence_score: float = Field(..., description="Confidence score 0-1")
    reason: str = Field(..., description="Reason for verification decision")


class GeminiAgent:
    """Agent for getting music recommendations using Google's Gemini AI"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash") -> None:
        genai.configure(api_key=api_key)
        system_instruction = self._build_system_prompt()
        self.model = genai.GenerativeModel(
            model_name,
            generation_config={
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 40,
            },
            system_instruction=system_instruction,
        )
        logger.info(f"Initialized Gemini Agent with model: {model_name}")

    def suggest(
        self, 
        seed_song: str, 
        count: int, 
        seed_artist: Optional[str] = None,
        seed_genre: Optional[str] = None,
        retries: int = 3
    ) -> List[SongSuggestion]:
        """
        Get song recommendations based on a seed song.
        
        Args:
            seed_song: The song to base recommendations on
            count: Number of recommendations to request
            seed_artist: Artist(s) of the seed song (from Spotify)
            seed_genre: Genre/style of the seed song (from Spotify)
            retries: Number of retry attempts on failure
            
        Returns:
            List of song suggestions
        """
        user_prompt = self._build_user_prompt(seed_song, count, seed_artist, seed_genre)
        
        for attempt in range(retries):
            try:
                logger.info(f"Requesting {count} recommendations from Gemini (attempt {attempt + 1}/{retries})...")
                response = self.model.generate_content(user_prompt)
                if not response or not response.text:
                    raise RuntimeError("Gemini returned an empty response")
                
                # Parse and validate the response
                payload = self._extract_and_validate_payload(response.text)
                
                if not payload.songs:
                    raise RuntimeError("Gemini did not return any song suggestions")
                
                logger.info(f"Successfully received {len(payload.songs)} suggestions")
                return payload.songs
                
            except (ValidationError, json.JSONDecodeError, RuntimeError) as exc:
                logger.warning(f"Attempt {attempt + 1} failed: {exc}")
                if attempt == retries - 1:
                    raise RuntimeError(f"Failed to get valid recommendations after {retries} attempts") from exc
                time.sleep(1)  # Brief delay before retry
        
        raise RuntimeError("Failed to get recommendations")

    @staticmethod
    def _build_system_prompt() -> str:
        return (
"You are an expert music recommendation assistant. Your task is to provide extremely relevant song recommendations by strictly following the steps below.\n\n"

        "**Step 1: Analyze the Seed Song**\n"
        "You will receive:\n"
        " - **Seed Song:** The exact title from Spotify\n"
        " - **Artist:** The verified artist(s) from Spotify\n"
        " - **Genre:** The genre/style from Spotify (when available)\n\n"
        "Use this verified information to understand:\n"
        " - **Core Genre/Culture:** (e.g., Punjabi Hip-Hop, Traditional Gujarati Folk, Bollywood Dance)\n"
        " - **Energy/Vibe:** (e.g., High-energy Club Banger, Devotional Raas, Melodic Pop-Fusion)\n"
        " - **Vocal Style:** (e.g., Energetic rap, Soulful singing, Folk vocals)\n\n"

        "**Step 2: Identify High-Confidence Matches**\n"
        " 1. **Same Artist Tracks:** Prioritize 2-3 most popular/sonically similar tracks by the **exact artist** provided.\n"
        " 2. **Direct Genre Matches:** Identify tracks by closely associated, high-production artists within the *exact* core genre.\n"
        "    - For Punjabi artists (e.g., Honey Singh, Guru Randhawa): suggest Badshah, Diljit Dosanjh, Hardy Sandhu\n"
        "    - For Gujarati folk (e.g., Aditya Gadhvi): suggest Kirtidan Gadhvi, Geeta Rabari, similar folk fusion\n"
        "    - For Bollywood: match energy/era/composer style\n"
        " 3. **Spotify Playability:** Ensure all suggested titles are extremely common and well-known to guarantee they resolve correctly on Spotify.\n\n"

        "**Step 3: Format the Output**\n"
        "Generate the recommendations in a clean JSON format. This is the ONLY output you must provide.\n\n"

        "### JSON Schema:\n"
            "{\n"
            '  "songs": [\n'
            "    {\n"
            '      "title": "exact song title as it appears on Spotify",\n'
            '      "artists": ["exact artist name(s) as on Spotify"],\n'
            '      "genre": "specific genre (e.g., Punjabi Club Anthem, Gujarati Folk Fusion, Bollywood Romantic)",\n'
            '      "reason": "1-2 lines explaining the direct sonic match (beat/vocal style/energy/production)"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            
         "🧠 **Critical Constraints:**\n"
        "- **The output MUST be clean, valid JSON ONLY.** No external text or markdown outside the JSON block.\n"
        "- Only suggest **extremely well-known, high-confidence** song titles that are guaranteed to be found on Spotify.\n"
        "- Use the **exact artist name** provided to find similar tracks by the same artist first.\n"
        "- Match the **genre and cultural context** precisely - don't mix Punjabi with Tamil, or Folk with EDM unless the seed does.\n"
        "- Avoid recommending the seed song itself or duplicates.\n\n"   
        )


    @staticmethod
    def _build_user_prompt(
        seed_song: str, 
        count: int, 
        seed_artist: Optional[str] = None, 
        seed_genre: Optional[str] = None
    ) -> str:
        prompt = f'Seed Song: "{seed_song}"\n'
        if seed_artist:
            prompt += f"Artist: {seed_artist}\n"
        if seed_genre:
            prompt += f"Genre: {seed_genre}\n"
        prompt += f"Number of Recommendations: {count}"
        return prompt

    @staticmethod
    def _extract_and_validate_payload(raw_text: str) -> SongRecommendations:
        """Extract and validate JSON from Gemini's response"""
        cleaned = raw_text.strip()
        
        # Remove markdown code blocks if present
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            cleaned = "\n".join(line for line in lines if not line.startswith("```"))
            cleaned = cleaned.strip()
        
        # Try parsing the cleaned text
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to extract JSON from the text
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start == -1 or end == -1:
                raise ValueError("No valid JSON found in response")
            snippet = cleaned[start : end + 1]
            data = json.loads(snippet)
        
        # Validate with Pydantic
        return SongRecommendations(**data)


class VerifierAgent:
    """Agent for verifying recommended songs match the seed song criteria"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash") -> None:
        genai.configure(api_key=api_key)
        system_instruction = self._build_system_prompt()
        self.model = genai.GenerativeModel(
            model_name,
            generation_config={
                "temperature": 0.3,  # Lower temperature for more consistent verification
                "top_p": 0.8,
                "top_k": 20,
            },
            system_instruction=system_instruction,
        )
        logger.info(f"Initialized Verifier Agent with model: {model_name}")
    
    def verify_recommendation(
        self,
        seed_song: str,
        seed_artist: str,
        seed_genre: Optional[str],
        recommended_song: SongSuggestion,
        recommended_track: Dict[str, Any]
    ) -> VerificationResult:
        """
        Verify if a recommended song matches the seed song criteria.
        
        Args:
            seed_song: Original seed song title
            seed_artist: Original seed artist(s)
            seed_genre: Original seed genre
            recommended_song: Recommended song from Gemini
            recommended_track: Spotify track data for the recommendation
            
        Returns:
            VerificationResult with validity decision
        """
        user_prompt = self._build_user_prompt(
            seed_song, seed_artist, seed_genre,
            recommended_song, recommended_track
        )
        
        try:
            response = self.model.generate_content(user_prompt)
            if not response or not response.text:
                logger.warning("Verifier returned empty response, assuming invalid")
                return VerificationResult(
                    is_valid=False,
                    confidence_score=0.0,
                    reason="Verification failed"
                )
            
            result = self._extract_and_validate_verification(response.text)
            return result
            
        except Exception as exc:
            logger.warning(f"Verification failed for {recommended_song.title}: {exc}")
            return VerificationResult(
                is_valid=False,
                confidence_score=0.0,
                reason=f"Verification error: {exc}"
            )
    
    @staticmethod
    def _build_system_prompt() -> str:
        return (
            "You are a music quality verifier. Your job is to determine if a recommended song "
            "is truly a good match for the seed song based on multiple criteria.\n\n"
            
            "**Evaluation Criteria:**\n"
            "1. **Artist Match (30%)**: Is it by the same artist, or a closely related artist in the same scene?\n"
            "2. **Genre/Culture Match (30%)**: Does it belong to the same genre and cultural context?\n"
            "   - Punjabi songs should stay with Punjabi\n"
            "   - Bollywood should match Bollywood era/style\n"
            "   - Folk should stay within the regional tradition\n"
            "3. **Energy/Vibe Match (20%)**: Does it have similar energy, tempo, and mood?\n"
            "4. **Popularity/Quality (10%)**: Is it a well-known, high-quality track likely to be on Spotify?\n"
            "5. **Sonic Coherence (10%)**: Would this song flow well after the seed in a playlist?\n\n"
            
            "**Your Task:**\n"
            "Evaluate the recommended song and return a JSON verdict.\n\n"
            
            "**Output Format (JSON ONLY):**\n"
            "{\n"
            '  "is_valid": true or false,\n'
            '  "confidence_score": 0.0 to 1.0,\n'
            '  "reason": "Brief explanation of why it passes or fails (1 sentence)"\n'
            "}\n\n"
            
            "**Rejection Reasons:**\n"
            "- Different language/culture (e.g., Punjabi seed but Tamil recommendation)\n"
            "- Completely different genre (e.g., Club banger seed but Classical recommendation)\n"
            "- Mismatched energy (e.g., High-energy seed but Slow ballad recommendation)\n"
            "- Artist has no connection to seed artist's scene\n"
            "- Unpopular/obscure track unlikely to be on Spotify\n\n"
            
            "**Acceptance Criteria:**\n"
            "- Same artist or closely associated artist (e.g., Honey Singh → Badshah)\n"
            "- Same genre and cultural context\n"
            "- Similar energy and production style\n"
            "- Well-known, popular track\n"
            "- Would create a cohesive listening experience"
        )
    
    @staticmethod
    def _build_user_prompt(
        seed_song: str,
        seed_artist: str,
        seed_genre: Optional[str],
        recommended_song: SongSuggestion,
        recommended_track: Dict[str, Any]
    ) -> str:
        rec_artists = ", ".join(artist["name"] for artist in recommended_track.get("artists", []))
        rec_popularity = recommended_track.get("popularity", 0)
        
        prompt = (
            "**Seed Song:**\n"
            f"- Title: {seed_song}\n"
            f"- Artist: {seed_artist}\n"
        )
        if seed_genre:
            prompt += f"- Genre: {seed_genre}\n"
        
        prompt += (
            "\n**Recommended Song:**\n"
            f"- Title: {recommended_song.title}\n"
            f"- Artist: {', '.join(recommended_song.artists)}\n"
            f"- Genre: {recommended_song.genre}\n"
            f"- AI Reason: {recommended_song.reason}\n"
            f"- Spotify Artist: {rec_artists}\n"
            f"- Spotify Popularity: {rec_popularity}/100\n"
            "\n**Question:** Is this recommended song a valid match for the seed song?"
        )
        
        return prompt
    
    @staticmethod
    def _extract_and_validate_verification(raw_text: str) -> VerificationResult:
        """Extract and validate verification result from response"""
        cleaned = raw_text.strip()
        
        # Remove markdown code blocks if present
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            cleaned = "\n".join(line for line in lines if not line.startswith("```"))
            cleaned = cleaned.strip()
        
        # Try parsing the cleaned text
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to extract JSON from the text
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start == -1 or end == -1:
                raise ValueError("No valid JSON found in verification response")
            snippet = cleaned[start : end + 1]
            data = json.loads(snippet)
        
        # Validate with Pydantic
        return VerificationResult(**data)


class SpotifyClient:
    """Client for interacting with Spotify API"""
    
    REQUIRED_SCOPE = "user-modify-playback-state user-read-playback-state user-read-currently-playing"
    
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
            scope=self.REQUIRED_SCOPE,
            cache_path=cache_path,
            open_browser=True,
        )
        self.client = spotipy.Spotify(auth_manager=self.oauth)
        logger.info("Initialized Spotify client")

    def resolve_track(
        self, 
        title: str, 
        artists: Optional[List[str]] = None,
        retries: int = 2
    ) -> Optional[Dict[str, Any]]:
        """
        Search for a track on Spotify.
        
        Args:
            title: Song title
            artists: Optional list of artist names
            retries: Number of retry attempts
            
        Returns:
            Track data if found, None otherwise
        """
        queries: List[str] = []

        # If freeform like "Title by Artist", parse into components
        parsed_title, parsed_artists = parse_title_and_artists_from_freeform(title)
        title_only = parsed_title
        artist_list = artists or parsed_artists

        # Build a broader set of queries
        if artist_list:
            for artist in artist_list:
                queries.append(f'track:"{title_only}" artist:"{artist}"')
        queries.append(f'track:"{title_only}"')
        queries.append(title_only)  # very broad fallback

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
                    # Early exit if a strong match found
                    if best_score >= 0.75:
                        return best
                except Exception as exc:
                    logger.warning(f"Search failed for '{query}': {exc}")
                    if attempt < retries - 1:
                        time.sleep(0.5)
        
        # Return best candidate if reasonably good
        if best and best_score >= 0.45:
            return best
        
        return None

    def add_to_queue(self, track_uri: str) -> bool:
        """
        Add a track to the Spotify queue.
        
        Args:
            track_uri: Spotify URI of the track
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.add_to_queue(track_uri)
            return True
        except Exception as exc:
            logger.error(f"Failed to add track to queue: {exc}")
            return False

    def start_playback(self, track_uri: str) -> bool:
        """
        Start playback of a track.
        
        Args:
            track_uri: Spotify URI of the track
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.start_playback(uris=[track_uri])
            return True
        except Exception as exc:
            logger.error(f"Failed to start playback: {exc}")
            return False

    def get_active_device(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active Spotify device.
        
        Returns:
            Device data if found, None otherwise
        """
        try:
            devices = self.client.devices().get("devices", [])
            for device in devices:
                if device.get("is_active"):
                    return device
            return devices[0] if devices else None
        except Exception as exc:
            logger.error(f"Failed to get devices: {exc}")
            return None

    def transfer_playback_to(self, device_id: str, play: bool = False) -> bool:
        """Transfer playback to a specific device to make it active."""
        try:
            self.client.transfer_playback(device_id=device_id, force_play=play)
            return True
        except Exception as exc:
            logger.error(f"Failed to transfer playback: {exc}")
            return False

    def ensure_active_device(self, seed_uri: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Ensure there is an active device. If none active, try to activate the first available
        device by transferring playback (without starting music), or optionally start playback
        of a provided seed track.
        """
        device = self.get_active_device()
        if device and device.get("is_active"):
            return device

        # Try to activate first available device
        try:
            devices = self.client.devices().get("devices", [])
        except Exception as exc:
            logger.error(f"Failed to list devices: {exc}")
            return None

        if not devices:
            return None

        target = devices[0]
        if seed_uri:
            # Starting playback will implicitly activate the device
            try:
                self.client.start_playback(device_id=target["id"], uris=[seed_uri])
                return target
            except Exception as exc:
                logger.warning(f"Starting playback to activate device failed: {exc}")

        # Fallback: transfer playback without forcing play
        if self.transfer_playback_to(target["id"], play=False):
            return target
        return None


def ensure_env_var(name: str) -> str:
    """Ensure an environment variable is set and return its value"""
    value = os.getenv(name)
    if not value:
        console.print(f"[red]✗[/red] Missing required environment variable: {name}")
        console.print("\n[yellow]Please set the following environment variables:[/yellow]")
        console.print("  - GOOGLE_API_KEY")
        console.print("  - SPOTIPY_CLIENT_ID")
        console.print("  - SPOTIPY_CLIENT_SECRET")
        console.print("  - SPOTIPY_REDIRECT_URI")
        console.print("\n[cyan]Tip: Create a .env file in the project directory[/cyan]")
        raise SystemExit(1)
    return value


def normalize_loopback_redirect_uri(raw_uri: str) -> str:
    """Normalize and validate redirect URI per Spotify's requirements.

    - localhost is NOT allowed; use 127.0.0.1 or [::1]
    - For loopback addresses, HTTP is permitted
    """
    parsed = urlparse(raw_uri)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid SPOTIPY_REDIRECT_URI format")

    host = parsed.hostname or ""
    # If user used localhost, switch to 127.0.0.1
    if host == "localhost":
        host = "127.0.0.1"

    # Validate loopback literal if HTTP is used
    if parsed.scheme == "http":
        if host not in ("127.0.0.1", "::1"):
            raise ValueError(
                "HTTP redirect URIs must use loopback IP literal (127.0.0.1 or [::1]) per Spotify"
            )

    # Rebuild URI with possibly updated host
    netloc = host
    if parsed.port:
        netloc = f"{host}:{parsed.port}"
    rebuilt = parsed._replace(netloc=netloc)
    return urlunparse(rebuilt)


def _normalize_text(value: str) -> str:
    """Lowercase and strip punctuation/extra spaces for robust comparisons."""
    value = value.lower()
    value = re.sub(r"[\(\)\[\]\{\}\.,!'\"]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _token_set_ratio(a: str, b: str) -> float:
    """Simple token-set similarity in [0,1]."""
    A = set(_normalize_text(a).split())
    B = set(_normalize_text(b).split())
    if not A or not B:
        return 0.0
    intersection = len(A & B)
    union = len(A | B)
    return intersection / union


def _artist_names_from_track(track: Dict[str, Any]) -> List[str]:
    return [a.get("name", "") for a in track.get("artists", [])]


def _score_track_match(title: str, artists: Optional[List[str]], track: Dict[str, Any]) -> float:
    """Score how well a Spotify track matches the desired title/artists.
    Combines title similarity, artist overlap, and a small popularity boost.
    """
    track_title = track.get("name", "")
    track_artists = _artist_names_from_track(track)

    title_score = _token_set_ratio(title, track_title)

    if artists:
        artist_target = " ".join(artists)
        artist_score = max((_token_set_ratio(artist_target, " ".join(track_artists))),  # all vs all
                           max((_token_set_ratio(a, " ".join(track_artists)) for a in artists), default=0.0))
    else:
        artist_score = 0.2  # slight default

    popularity = (track.get("popularity", 0) or 0) / 100.0

    # Weighted score
    score = 0.65 * title_score + 0.3 * artist_score + 0.05 * popularity
    
    # Small boost for exact-ish prefix matches
    if _normalize_text(track_title).startswith(_normalize_text(title)[:10]):
        score += 0.05

    return min(score, 1.0)


def parse_title_and_artists_from_freeform(text: str) -> tuple[str, Optional[List[str]]]:
    """Parse inputs like 'Lahore by Guru Randhawa' or 'Song - Artist'."""
    parts = re.split(r"\s+by\s+|\s+-\s+|\s+–\s+|\s+—\s+|\s*\|\s*", text, flags=re.IGNORECASE)
    title = parts[0].strip()
    artists: Optional[List[str]] = None
    if len(parts) > 1:
        # Split multiple artists by common delimiters
        artists = re.split(r",|&|feat\.?|ft\.?|with", parts[1], flags=re.IGNORECASE)
        artists = [a.strip() for a in artists if a.strip()]
        if not artists:
            artists = None
    return title, artists


def display_recommendations_table(queue_plan: List[tuple[SongSuggestion, Dict[str, Any]]]) -> None:
    """Display recommendations in a formatted table"""
    table = Table(title="🎵 Recommended Songs", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Song", style="cyan", width=30)
    table.add_column("Artist(s)", style="green", width=25)
    table.add_column("Genre", style="yellow", width=15)
    table.add_column("Reason", style="white", width=40)
    
    for idx, (suggestion, track) in enumerate(queue_plan, 1):
        artists = ", ".join(artist["name"] for artist in track["artists"])
        table.add_row(
            str(idx),
            track["name"][:28] + "..." if len(track["name"]) > 30 else track["name"],
            artists[:23] + "..." if len(artists) > 25 else artists,
            suggestion.genre or "N/A",
            (suggestion.reason[:38] + "...") if suggestion.reason and len(suggestion.reason) > 40 else (suggestion.reason or "")
        )
    
    console.print(table)


def main() -> None:
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(
        description="🎵 Spotify Music Recommendation System - Powered by Gemini AI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--song", 
        help="Seed song title (you'll be prompted if not provided)"
    )
    parser.add_argument(
        "--count", 
        type=int, 
        default=5, 
        help="Number of recommendations to request (default: 5)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Only show recommendations without modifying Spotify queue"
    )
    parser.add_argument(
        "--autoplay", 
        action="store_true", 
        help="Automatically start playback of the seed song"
    )
    parser.add_argument(
        "--redirect-uri",
        help="Override redirect URI (use loopback IP literal, e.g., http://127.0.0.1:8888/callback)",
    )
    parser.add_argument(
        "--verbose", 
        "-v", 
        action="store_true", 
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        default=True,
        help="Enable AI verification of recommendations (default: True)"
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Disable AI verification of recommendations"
    )
    args = parser.parse_args()
    
    # Handle verify flag
    if args.no_verify:
        args.verify = False
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Display banner
    console.print(Panel.fit(
        "[bold cyan]🎵 Spotify Music Recommendation System[/bold cyan]\n"
        "[dim]Powered by Gemini AI[/dim]",
        border_style="cyan"
    ))
    
    # Get seed song
    seed_song = args.song
    if not seed_song:
        seed_song = console.input("[bold green]Enter a song name:[/bold green] ").strip()
    
    if not seed_song:
        console.print("[red]✗ Song name is required[/red]")
        raise SystemExit(1)
    
    console.print(f"\n[cyan]Seed Song:[/cyan] {seed_song}")
    
    # Load environment variables
    try:
        google_key = ensure_env_var("GOOGLE_API_KEY")
        spotify_client_id = ensure_env_var("SPOTIPY_CLIENT_ID")
        spotify_client_secret = ensure_env_var("SPOTIPY_CLIENT_SECRET")
        spotify_redirect_uri = args.redirect_uri or ensure_env_var("SPOTIPY_REDIRECT_URI")
        try:
            spotify_redirect_uri = normalize_loopback_redirect_uri(spotify_redirect_uri)
        except ValueError as exc:
            console.print(f"[red]✗ Invalid redirect URI:[/red] {exc}")
            console.print("[yellow]Use a loopback IP literal such as http://127.0.0.1:8888/callback[/yellow]")
            raise SystemExit(1)
    except SystemExit:
        raise
    
    # Initialize clients
    try:
        gemini = GeminiAgent(google_key)
        verifier = VerifierAgent(google_key) if args.verify else None
        spotify = SpotifyClient(
            client_id=spotify_client_id,
            client_secret=spotify_client_secret,
            redirect_uri=spotify_redirect_uri,
        )
        
        if args.verify:
            console.print("[cyan]ℹ AI Verification enabled - recommendations will be validated[/cyan]")
    except Exception as exc:
        console.print(f"[red]✗ Failed to initialize clients: {exc}[/red]")
        raise SystemExit(1)
    
    # Resolve seed track on Spotify first to get metadata
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Searching for '{seed_song}' on Spotify...", total=None)
        seed_track = spotify.resolve_track(seed_song)
        progress.remove_task(task)
    
    if not seed_track:
        console.print(f"[red]✗ Could not find '{seed_song}' on Spotify[/red]")
        raise SystemExit(1)
    
    seed_uri = seed_track["uri"]
    seed_artists = ", ".join(artist["name"] for artist in seed_track["artists"])
    seed_track_name = seed_track["name"]
    
    # Extract genre information (Spotify doesn't always provide genre in track, so we get from album or use a fallback)
    seed_genre = None
    if "album" in seed_track and "genres" in seed_track["album"]:
        genres = seed_track["album"].get("genres", [])
        if genres:
            seed_genre = ", ".join(genres[:2])  # Take first 2 genres
    
    console.print(f"[green]✓[/green] Found: [bold]{seed_track_name}[/bold] by {seed_artists}")
    if seed_genre:
        console.print(f"[dim]Genre: {seed_genre}[/dim]\n")
    else:
        console.print()
    
    # Get recommendations from Gemini with enriched metadata
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Getting recommendations from Gemini AI...", total=None)
        try:
            suggestions = gemini.suggest(
                seed_song=seed_track_name,
                count=args.count,
                seed_artist=seed_artists,
                seed_genre=seed_genre
            )
        except Exception as exc:
            console.print(f"\n[red]✗ Failed to get recommendations: {exc}[/red]")
            raise SystemExit(1)
        finally:
            progress.remove_task(task)
    
    console.print(f"[green]✓[/green] Received {len(suggestions)} suggestions from Gemini\n")
    
    # Resolve and verify recommended tracks on Spotify
    queue_plan: List[tuple[SongSuggestion, Dict[str, Any]]] = []
    verified_count = 0
    rejected_count = 0
    
    task_desc = "Verifying and resolving recommendations..." if verifier else "Resolving recommendations on Spotify..."
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(task_desc, total=len(suggestions))
        
        for suggestion in suggestions:
            # Use fuzzy resolution for LLM outputs
            track = spotify.resolve_track(suggestion.title, suggestion.artists)
            if not track:
                logger.warning(f"Could not find on Spotify: {suggestion.title}")
                progress.advance(task)
                continue
            
            # Verify recommendation if verifier is enabled
            if verifier:
                verification = verifier.verify_recommendation(
                    seed_song=seed_track_name,
                    seed_artist=seed_artists,
                    seed_genre=seed_genre,
                    recommended_song=suggestion,
                    recommended_track=track
                )
                
                if verification.is_valid:
                    queue_plan.append((suggestion, track))
                    verified_count += 1
                    logger.debug(f"✓ Verified: {track['name']} (score: {verification.confidence_score:.2f})")
                else:
                    rejected_count += 1
                    logger.info(f"✗ Rejected: {track['name']} - {verification.reason}")
            else:
                # No verification, add directly
                queue_plan.append((suggestion, track))
                logger.debug(f"Resolved: {track['name']}")
            
            progress.advance(task)
    
    if not queue_plan:
        console.print("[red]✗ No valid songs from the recommendations[/red]")
        if verifier and rejected_count > 0:
            console.print(f"[yellow]All {rejected_count} recommendations were rejected by the verifier[/yellow]")
        raise SystemExit(1)
    
    result_msg = f"[green]✓[/green] Resolved {len(queue_plan)}/{len(suggestions)} tracks on Spotify"
    if verifier:
        result_msg += f" ([green]{verified_count} verified[/green], [red]{rejected_count} rejected[/red])"
    console.print(result_msg + "\n")
    
    # Display recommendations
    display_recommendations_table(queue_plan)
    
    # Add to queue or dry run
    if args.dry_run:
        console.print("\n[yellow]Dry run mode - no changes made to Spotify[/yellow]")
        return
    
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Adding songs to Spotify queue...", total=len(queue_plan))
        
        success_count = 0
        # Ensure there is an active device before queueing
        active_device = spotify.ensure_active_device(seed_uri)
        if not active_device:
            console.print("[yellow]⚠ No active Spotify device found. Open Spotify on any device.[/yellow]")
        
        for suggestion, track in queue_plan:
            added = spotify.add_to_queue(track["uri"])  # First attempt
            if not added:
                # If failed due to no active device, try to ensure device and retry once
                active_device = spotify.ensure_active_device()
                if active_device:
                    added = spotify.add_to_queue(track["uri"])  # Retry once after activating device
            if added:
                success_count += 1
            progress.advance(task)
            time.sleep(0.1)  # Small delay to avoid rate limiting
    
    console.print(f"[green]✓[/green] Successfully added {success_count}/{len(queue_plan)} songs to queue\n")
    
    # Start playback if requested
    if args.autoplay:
        device = spotify.get_active_device()
        if not device:
            console.print("[yellow]⚠ No active Spotify device found[/yellow]")
            console.print("[dim]Please open Spotify and start playback manually[/dim]")
        else:
            if spotify.start_playback(seed_uri):
                console.print(f"[green]✓[/green] Started playback on [bold]{device['name']}[/bold]")
            else:
                console.print("[yellow]⚠ Could not start playback automatically[/yellow]")
    else:
        console.print("[cyan]ℹ[/cyan] Songs added to queue. Start playback on your Spotify device.")
    
    console.print("\n[bold green]Done! Enjoy your music! 🎶[/bold green]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Aborted by user[/yellow]")
        raise SystemExit(130)
    except Exception as exc:
        console.print(f"\n[red]Fatal error: {exc}[/red]")
        logger.exception("Unexpected error occurred")
        raise SystemExit(1)

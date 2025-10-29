"""Pydantic models for API requests and responses"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SongSuggestion(BaseModel):
    """Model for a song suggestion"""
    title: str = Field(..., description="Song title")
    artists: List[str] = Field(..., description="List of artist names")
    genre: Optional[str] = Field(None, description="Music genre")
    reason: Optional[str] = Field(None, description="Reason for recommendation")


class SongRecommendations(BaseModel):
    """Model for a list of song suggestions from Gemini"""
    songs: List[SongSuggestion] = Field(..., description="List of song recommendations")


class VerificationResult(BaseModel):
    """Model for song verification result"""
    is_valid: bool = Field(..., description="Whether the song is a valid recommendation")
    confidence_score: float = Field(..., description="Confidence score 0-1")
    reason: str = Field(..., description="Reason for verification decision")


class SpotifyTrack(BaseModel):
    """Simplified Spotify track model"""
    id: str
    name: str
    artists: List[str]
    album: str
    uri: str
    popularity: int
    preview_url: Optional[str] = None
    image_url: Optional[str] = None


class RecommendationRequest(BaseModel):
    """Request model for getting recommendations"""
    seed_song: str = Field(..., description="Seed song name or 'Title by Artist'")
    count: int = Field(5, ge=1, description="Number of recommendations")
    verify: bool = Field(True, description="Enable AI verification")


class RecommendationResponse(BaseModel):
    """Response model for recommendations"""
    seed_track: SpotifyTrack
    recommendations: List[dict]  # List of {suggestion, track, verification}
    total_found: int
    total_verified: int
    total_rejected: int


class QueueRequest(BaseModel):
    """Request model for adding songs to queue"""
    track_uris: List[str] = Field(..., description="List of Spotify track URIs")
    autoplay: bool = Field(False, description="Start playback automatically")


class QueueResponse(BaseModel):
    """Response model for queue operation"""
    success: bool
    added_count: int
    message: str


class SpotifyAuthResponse(BaseModel):
    """Response model for Spotify authentication"""
    auth_url: str
    message: str


class SpotifyCallbackRequest(BaseModel):
    """Request model for Spotify OAuth callback"""
    code: str
    state: Optional[str] = None


class SpotifyTokenResponse(BaseModel):
    """Response model for Spotify token"""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    services: dict


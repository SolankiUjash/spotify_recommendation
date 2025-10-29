"""Async Verifier Agent"""

import json
import logging
from typing import Dict, Any, Optional, List
import google.generativeai as genai
import asyncio

from app.models.schemas import SongSuggestion, VerificationResult

logger = logging.getLogger(__name__)


class VerifierAgentAsync:
    """Async agent for verifying recommended songs match the seed song criteria"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash") -> None:
        genai.configure(api_key=api_key)
        system_instruction = self._build_system_prompt()
        self.model = genai.GenerativeModel(
            model_name,
            generation_config={
                "temperature": 0.3,
                "top_p": 0.8,
                "top_k": 20,
            },
            system_instruction=system_instruction,
        )
        logger.info(f"Initialized Async Verifier Agent with model: {model_name}")
    
    async def verify_batch(
        self,
        seed_song: str,
        seed_artist: str,
        seed_genre: Optional[str],
        recommendations: List[tuple]  # List of (SongSuggestion, track_dict)
    ) -> List[VerificationResult]:
        """Verify multiple recommendations in a single API call"""
        user_prompt = self._build_batch_prompt(
            seed_song, seed_artist, seed_genre, recommendations
        )
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                user_prompt
            )
            
            if not response or not response.text:
                logger.warning("Batch verifier returned empty response")
                return [VerificationResult(is_valid=True, confidence_score=0.5, reason="Verification skipped") for _ in recommendations]
            
            result = self._extract_batch_verification(response.text, len(recommendations))
            return result
            
        except Exception as exc:
            logger.warning(f"Batch verification failed: {exc}")
            return [VerificationResult(is_valid=True, confidence_score=0.5, reason=f"Verification error: {str(exc)[:50]}") for _ in recommendations]
    
    async def verify_recommendation(
        self,
        seed_song: str,
        seed_artist: str,
        seed_genre: Optional[str],
        recommended_song: SongSuggestion,
        recommended_track: Dict[str, Any]
    ) -> VerificationResult:
        """Async verification of a recommendation"""
        user_prompt = self._build_user_prompt(
            seed_song, seed_artist, seed_genre,
            recommended_song, recommended_track
        )
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                user_prompt
            )
            
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
        
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            cleaned = "\n".join(line for line in lines if not line.startswith("```"))
            cleaned = cleaned.strip()
        
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start == -1 or end == -1:
                raise ValueError("No valid JSON found in verification response")
            snippet = cleaned[start : end + 1]
            data = json.loads(snippet)
        
        return VerificationResult(**data)
    
    @staticmethod
    def _build_batch_prompt(
        seed_song: str,
        seed_artist: str,
        seed_genre: Optional[str],
        recommendations: List[tuple]
    ) -> str:
        """Build prompt for batch verification"""
        prompt = f"""**Seed Song:**
- Title: {seed_song}
- Artist: {seed_artist}"""
        
        if seed_genre:
            prompt += f"\n- Genre: {seed_genre}"
        
        prompt += "\n\n**Recommended Songs to Verify:**\n\n"
        
        for idx, (suggestion, track) in enumerate(recommendations, 1):
            rec_artists = ", ".join(artist["name"] for artist in track.get("artists", []))
            rec_popularity = track.get("popularity", 0)
            
            prompt += f"""{idx}. {suggestion.title}
   - Artist: {', '.join(suggestion.artists)}
   - Genre: {suggestion.genre}
   - Spotify Artist: {rec_artists}
   - Popularity: {rec_popularity}/100
   - AI Reason: {suggestion.reason}

"""
        
        prompt += """
**Task:** Verify ALL songs in a single response. Return JSON array with verification for each song IN ORDER.

**Output Format (JSON ONLY):**
{
  "verifications": [
    {"song_number": 1, "is_valid": true, "confidence_score": 0.95, "reason": "Same artist, matching style"},
    {"song_number": 2, "is_valid": false, "confidence_score": 0.3, "reason": "Different genre"},
    ...
  ]
}

Return ONLY valid JSON. Verify all songs based on:
- Artist/Genre match with seed
- Energy/vibe similarity
- Cultural context match
"""
        
        return prompt
    
    @staticmethod
    def _extract_batch_verification(raw_text: str, expected_count: int) -> List[VerificationResult]:
        """Extract and validate batch verification results"""
        cleaned = raw_text.strip()
        
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            cleaned = "\n".join(line for line in lines if not line.startswith("```"))
            cleaned = cleaned.strip()
        
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start == -1 or end == -1:
                logger.warning("No valid JSON in batch verification")
                return [VerificationResult(is_valid=True, confidence_score=0.5, reason="Parse error") for _ in range(expected_count)]
            snippet = cleaned[start : end + 1]
            data = json.loads(snippet)
        
        verifications = data.get("verifications", [])
        results = []
        
        for i in range(expected_count):
            if i < len(verifications):
                v = verifications[i]
                results.append(VerificationResult(
                    is_valid=v.get("is_valid", True),
                    confidence_score=v.get("confidence_score", 0.5),
                    reason=v.get("reason", "Verified")
                ))
            else:
                results.append(VerificationResult(is_valid=True, confidence_score=0.5, reason="Missing result"))
        
        return results


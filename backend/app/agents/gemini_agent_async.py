"""Async Gemini Agent with streaming support"""

import json
import logging
from typing import List, Optional, AsyncGenerator
import google.generativeai as genai
from pydantic import ValidationError
import asyncio

from app.models.schemas import SongSuggestion, SongRecommendations

logger = logging.getLogger(__name__)


class GeminiAgentAsync:
    """Async agent for getting music recommendations using Google's Gemini AI with streaming"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash") -> None:
        genai.configure(api_key=api_key)
        system_instruction = self._build_system_prompt()
        self.model = genai.GenerativeModel(
            model_name,
            generation_config={
                "temperature": 0.6,
                "top_p": 0.95,
                "top_k": 40,
                "response_mime_type": "application/json",
            },
            system_instruction=system_instruction,
        )
        logger.info(f"Initialized Async Gemini Agent with model: {model_name}")

    async def suggest_stream(
        self, 
        seed_song: str, 
        count: int, 
        seed_artist: Optional[str] = None,
        seed_genre: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Stream song recommendations as they're generated.
        
        Yields:
            dict: Status updates and partial/complete suggestions
        """
        user_prompt = self._build_user_prompt(seed_song, count, seed_artist, seed_genre)
        
        yield {"type": "status", "message": "Requesting recommendations from Gemini..."}
        
        try:
            # Use generate_content with stream=True for async streaming
            response = await asyncio.to_thread(
                self.model.generate_content,
                user_prompt,
                stream=True
            )
            
            accumulated_text = ""
            
            # Stream chunks as they arrive
            for chunk in response:
                if chunk.text:
                    accumulated_text += chunk.text
                    yield {
                        "type": "chunk",
                        "text": chunk.text,
                        "accumulated": accumulated_text
                    }
            
            # Parse final accumulated response
            yield {"type": "status", "message": "Parsing recommendations..."}
            
            payload = self._extract_and_validate_payload(accumulated_text)
            
            if not payload.songs:
                raise RuntimeError("Gemini did not return any song suggestions")
            
            logger.info(f"Successfully received {len(payload.songs)} suggestions")
            
            yield {
                "type": "complete",
                "suggestions": [s.dict() for s in payload.songs],
                "count": len(payload.songs)
            }
            
        except Exception as exc:
            logger.error(f"Error in streaming suggestions: {exc}", exc_info=True)
            yield {
                "type": "error",
                "error": str(exc)
            }

    async def suggest(
        self, 
        seed_song: str, 
        count: int, 
        seed_artist: Optional[str] = None,
        seed_genre: Optional[str] = None,
        retries: int = 3
    ) -> List[SongSuggestion]:
        """
        Get song recommendations (non-streaming version for compatibility).
        """
        user_prompt = self._build_user_prompt(seed_song, count, seed_artist, seed_genre)
        
        for attempt in range(retries):
            try:
                logger.info(f"Requesting {count} recommendations from Gemini (attempt {attempt + 1}/{retries})...")
                
                # Run in thread pool to avoid blocking
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    user_prompt
                )
                
                if not response or not response.text:
                    raise RuntimeError("Gemini returned an empty response")
                
                payload = self._extract_and_validate_payload(response.text)
                
                if not payload.songs:
                    raise RuntimeError("Gemini did not return any song suggestions")
                
                logger.info(f"Successfully received {len(payload.songs)} suggestions")
                return payload.songs
                
            except (ValidationError, json.JSONDecodeError, RuntimeError) as exc:
                logger.warning(f"Attempt {attempt + 1} failed: {exc}")
                if attempt == retries - 1:
                    raise RuntimeError(f"Failed to get valid recommendations after {retries} attempts") from exc
                await asyncio.sleep(1)
        
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
        prompt += f"\n**IMPORTANT: You MUST provide EXACTLY {count} song recommendations. Not less, not more. Return {count} songs.**\n"
        prompt += f"Number of Recommendations Required: {count}"
        return prompt

    @staticmethod
    def _extract_and_validate_payload(raw_text: str) -> SongRecommendations:
        """Extract and validate JSON from Gemini's response with robust fallbacks."""
        text = raw_text.strip()

        # 1) Extract fenced code blocks first (prefer ```json)
        if "```" in text:
            blocks = []
            current = []
            fenced = False
            fence_lang = None
            for line in text.splitlines():
                if line.strip().startswith("```"):
                    if not fenced:
                        fenced = True
                        fence_lang = line.strip().strip("`").lower()
                        current = []
                    else:
                        content = "\n".join(current).strip()
                        blocks.append((fence_lang or "", content))
                        fenced = False
                        fence_lang = None
                elif fenced:
                    current.append(line)

            # Try json-labeled blocks first
            for lang, content in blocks:
                if "json" in lang:
                    try:
                        data = json.loads(content)
                        return SongRecommendations(**data)
                    except Exception:
                        pass
            # Then any fenced block
            for _, content in blocks:
                try:
                    data = json.loads(content)
                    return SongRecommendations(**data)
                except Exception:
                    pass

        # 2) Try direct parse
        try:
            data = json.loads(text)
            return SongRecommendations(**data)
        except Exception:
            pass

        # 3) Locate most plausible JSON object containing "songs" using brace matching
        candidates = []
        stack = []
        starts = []
        for i, ch in enumerate(text):
            if ch == '{':
                stack.append('{')
                starts.append(i)
            elif ch == '}' and stack:
                stack.pop()
                start = starts.pop()
                snippet = text[start:i+1]
                if '"songs"' in snippet or 'songs' in snippet:
                    candidates.append(snippet)
        candidates.sort(key=len, reverse=True)
        for snippet in candidates:
            try:
                data = json.loads(snippet)
                return SongRecommendations(**data)
            except Exception:
                continue

        # 4) Give a concise error with excerpt for logs
        excerpt = text[:300].replace('\n', ' ')
        raise ValueError(f"No valid JSON found in response. Excerpt: {excerpt}")


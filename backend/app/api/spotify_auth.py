"""Spotify authentication endpoints"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Response, Request
from fastapi.responses import RedirectResponse, JSONResponse
from app.models.schemas import SpotifyAuthResponse
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

COOKIE_ACCESS = "spotify_access_token"
COOKIE_REFRESH = "spotify_refresh_token"
COOKIE_EXPIRES = "spotify_expires_at"

COOKIE_OPTS = {
  "httponly": True,
  "secure": True,  # required for cross-site cookies via Cloudflare tunnel (https)
  "samesite": "none",
  "path": "/",
}


@router.get("/spotify/auth-url", response_model=SpotifyAuthResponse)
async def get_spotify_auth_url():
    """
    Get Spotify OAuth authorization URL
    
    Returns the URL that the frontend should redirect to for user authentication
    """
    try:
        from spotipy.oauth2 import SpotifyOAuth
        from spotipy.exceptions import SpotifyOauthError
        from spotipy.exceptions import SpotifyOauthError
        
        oauth = SpotifyOAuth(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            redirect_uri=settings.spotify_redirect_uri,
            scope="user-modify-playback-state user-read-playback-state user-read-currently-playing",
            show_dialog=False
        )
        
        auth_url = oauth.get_authorize_url()
        
        return SpotifyAuthResponse(
            auth_url=auth_url,
            message="Redirect user to this URL for Spotify authentication"
        )
        
    except Exception as exc:
        logger.error(f"Error generating auth URL: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/spotify/login")
async def spotify_login():
    """Redirect the user agent to Spotify's authorization page."""
    from spotipy.oauth2 import SpotifyOAuth

    oauth = SpotifyOAuth(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_redirect_uri,
        scope="user-modify-playback-state user-read-playback-state user-read-currently-playing",
        show_dialog=False,
    )
    return RedirectResponse(oauth.get_authorize_url(), status_code=302)


@router.get("/spotify/callback")
async def spotify_callback_get(request: Request, response: Response, code: str, state: str | None = None):
    """
    Handle Spotify OAuth callback (GET). Exchanges authorization code for tokens
    and sets them as HTTP-only cookies for subsequent requests.
    """
    try:
        from spotipy.oauth2 import SpotifyOAuth
        from spotipy.exceptions import SpotifyOauthError

        oauth = SpotifyOAuth(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            redirect_uri=settings.spotify_redirect_uri,
            scope="user-modify-playback-state user-read-playback-state user-read-currently-playing",
        )

        try:
            token_info = oauth.get_access_token(code, as_dict=True, check_cache=False)
        except SpotifyOauthError as oauth_err:
            # Handle common error when code is reused/expired by redirect races
            msg = str(oauth_err)
            logger.warning(f"OAuth error during token exchange: {msg}")
            if "invalid_grant" in msg:
                # Re-initiate login cleanly
                login_url = SpotifyOAuth(
                    client_id=settings.spotify_client_id,
                    client_secret=settings.spotify_client_secret,
                    redirect_uri=settings.spotify_redirect_uri,
                    scope="user-modify-playback-state user-read-playback-state user-read-currently-playing",
                    show_dialog=True,
                ).get_authorize_url()
                return RedirectResponse(login_url, status_code=302)
            raise
        if not token_info:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        access_token = token_info["access_token"]
        refresh_token = token_info.get("refresh_token")
        expires_in = int(token_info.get("expires_in", 3600))
        expires_at = int((datetime.utcnow() + timedelta(seconds=expires_in - 30)).timestamp())

        # Determine frontend URL (configured or same host)
        frontend_url = getattr(settings, "frontend_base_url", None)
        if not frontend_url:
            scheme = request.url.scheme
            host = request.url.hostname
            port = request.url.port
            # Build absolute origin from current request
            if port and port not in (80, 443):
                frontend_url = f"{scheme}://{host}:{port}"
            else:
                frontend_url = f"{scheme}://{host}"

        # Build redirect response and SET COOKIES ON IT (not on the unused Response)
        redirect_resp = RedirectResponse(frontend_url, status_code=303)

        # Compute cookie domain from frontend_url (not request host)
        # Extract domain from frontend_url for proper cookie scope
        cookie_domain = None
        try:
            from urllib.parse import urlparse
            parsed = urlparse(frontend_url)
            host = parsed.hostname or ""
            # Only set domain if it's a real domain (not localhost/IP)
            if host and not host.startswith("127.") and host not in ("localhost", "0.0.0.0") and not any(c.isdigit() for c in host.replace(".", "")):
                cookie_domain = host
                logger.info(f"Setting cookies for domain: {cookie_domain}")
        except Exception as e:
            logger.warning(f"Failed to parse frontend URL for cookie domain: {e}")

        cookie_kwargs = {**COOKIE_OPTS}
        if cookie_domain:
            cookie_kwargs["domain"] = cookie_domain
        
        logger.info(f"Setting cookies with domain={cookie_domain}, secure={cookie_kwargs.get('secure')}, samesite={cookie_kwargs.get('samesite')}")

        redirect_resp.set_cookie(COOKIE_ACCESS, access_token, max_age=expires_in, **cookie_kwargs)
        if refresh_token:
            redirect_resp.set_cookie(COOKIE_REFRESH, refresh_token, max_age=30*24*3600, **cookie_kwargs)
        redirect_resp.set_cookie(COOKIE_EXPIRES, str(expires_at), max_age=expires_in, **cookie_kwargs)
        
        logger.info(f"Redirecting to {frontend_url} with cookies set")
        return redirect_resp

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in OAuth callback: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/spotify/callback")
async def spotify_callback(code: str):
    """
    Backward-compatible POST callback: returns tokens in JSON (used by CLI).
    """
    try:
        from spotipy.oauth2 import SpotifyOAuth
        
        oauth = SpotifyOAuth(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            redirect_uri=settings.spotify_redirect_uri,
            scope="user-modify-playback-state user-read-playback-state user-read-currently-playing"
        )
        
        token_info = oauth.get_access_token(code, as_dict=True, check_cache=False)
        
        if not token_info:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        return {
            "access_token": token_info["access_token"],
            "token_type": token_info["token_type"],
            "expires_in": token_info["expires_in"],
            "refresh_token": token_info.get("refresh_token"),
            "scope": token_info.get("scope")
        }
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in OAuth callback: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/spotify/refresh")
async def refresh_token(request: Request):
    """Refresh the Spotify access token using the refresh token cookie."""
    try:
        from spotipy.oauth2 import SpotifyOAuth

        refresh_token_cookie = request.cookies.get(COOKIE_REFRESH)
        if not refresh_token_cookie:
            raise HTTPException(status_code=401, detail="No refresh token cookie found")

        oauth = SpotifyOAuth(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            redirect_uri=settings.spotify_redirect_uri,
            scope="user-modify-playback-state user-read-playback-state user-read-currently-playing",
        )

        token_info = oauth.refresh_access_token(refresh_token_cookie)
        if not token_info:
            raise HTTPException(status_code=400, detail="Failed to refresh access token")

        access_token = token_info["access_token"]
        expires_in = int(token_info.get("expires_in", 3600))
        expires_at = int((datetime.utcnow() + timedelta(seconds=expires_in - 30)).timestamp())

        # Align cookie domain with frontend like in GET callback
        frontend_url = getattr(settings, "frontend_base_url", None)
        if not frontend_url:
            # Try Origin header if present
            origin = request.headers.get("Origin")
            if origin:
                frontend_url = origin
            else:
                # Fallback to request host
                scheme = request.url.scheme
                host = request.url.hostname
                port = request.url.port
                if port and port not in (80, 443):
                    frontend_url = f"{scheme}://{host}:{port}"
                else:
                    frontend_url = f"{scheme}://{host}"

        cookie_domain = None
        try:
            from urllib.parse import urlparse
            parsed = urlparse(frontend_url)
            host = parsed.hostname or ""
            if host and host not in ("localhost", "0.0.0.0") and not host.startswith("127.") and not any(c.isdigit() for c in host.replace(".", "")):
                cookie_domain = host
        except Exception:
            cookie_domain = None

        cookie_kwargs = {**COOKIE_OPTS}
        if cookie_domain:
            cookie_kwargs["domain"] = cookie_domain

        resp = JSONResponse({"ok": True})
        resp.set_cookie(COOKIE_ACCESS, access_token, max_age=expires_in, **cookie_kwargs)
        resp.set_cookie(COOKIE_EXPIRES, str(expires_at), max_age=expires_in, **cookie_kwargs)
        return resp
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error refreshing token: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))



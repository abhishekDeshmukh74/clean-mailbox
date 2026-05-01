from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from ..config import get_settings
from .session import (
    SESSION_COOKIE,
    encrypt,
    save_user_tokens,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.modify",
]

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def _require_creds() -> None:
    settings = get_settings()
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )


@router.get("/login")
def login() -> RedirectResponse:
    _require_creds()
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
    }
    return RedirectResponse(f"{AUTH_URL}?{urlencode(params)}")


@router.get("/callback")
def callback(request: Request) -> RedirectResponse:
    _require_creds()
    settings = get_settings()

    err = request.query_params.get("error")
    if err:
        raise HTTPException(status_code=400, detail=f"OAuth error: {err}")

    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    # Direct token exchange — avoids scope-validation quirks in oauthlib.
    try:
        token_resp = httpx.post(
            TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=15.0,
        )
    except httpx.HTTPError as exc:
        logger.exception("Token endpoint request failed")
        raise HTTPException(status_code=502, detail=f"Token exchange failed: {exc}") from exc

    if token_resp.status_code != 200:
        logger.error(
            "Token exchange rejected: status=%s body=%s",
            token_resp.status_code,
            token_resp.text,
        )
        raise HTTPException(
            status_code=400,
            detail=(
                "Google rejected the authorization code. Most common causes: "
                "(1) redirect_uri in Google Cloud Console must EXACTLY match "
                f"'{settings.google_redirect_uri}'; (2) the code may have been used twice "
                "(do not refresh /auth/callback). "
                f"Google said: {token_resp.text[:300]}"
            ),
        )

    tok = token_resp.json()
    access_token = tok.get("access_token")
    refresh_token = tok.get("refresh_token")
    expires_in = int(tok.get("expires_in", 3600))
    granted_scopes = (tok.get("scope") or " ".join(SCOPES)).split()

    if not access_token:
        raise HTTPException(status_code=400, detail="No access_token in token response")

    # Fetch user identity.
    userinfo: dict = {}
    try:
        u = httpx.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )
        if u.status_code == 200:
            userinfo = u.json()
        else:
            logger.warning("userinfo failed: %s %s", u.status_code, u.text[:200])
    except httpx.HTTPError as exc:
        logger.warning("userinfo request error: %s", exc)

    sub = userinfo.get("sub") or userinfo.get("email") or "unknown"
    expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    save_user_tokens(
        sub,
        {
            "sub": sub,
            "email": userinfo.get("email"),
            "name": userinfo.get("name"),
            "picture": userinfo.get("picture"),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_uri": TOKEN_URL,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "scopes": granted_scopes,
            "expiry": expiry.isoformat(),
            "saved_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    response = RedirectResponse(settings.frontend_url)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=encrypt({"sub": sub, "email": userinfo.get("email")}),
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        samesite="lax",
        secure=False,  # set True behind HTTPS
        path="/",
    )
    return response


@router.get("/logout")
def logout() -> Response:
    settings = get_settings()
    response = RedirectResponse(settings.frontend_url)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response

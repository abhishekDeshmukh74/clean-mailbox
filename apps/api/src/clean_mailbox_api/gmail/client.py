from __future__ import annotations

from datetime import datetime

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from ..auth.session import load_user_tokens, save_user_tokens


def _credentials_from_payload(payload: dict) -> Credentials:
    expiry = None
    if payload.get("expiry"):
        try:
            expiry = datetime.fromisoformat(payload["expiry"])
            if expiry.tzinfo is not None:
                expiry = expiry.replace(tzinfo=None)
        except ValueError:
            expiry = None
    creds = Credentials(
        token=payload.get("access_token"),
        refresh_token=payload.get("refresh_token"),
        token_uri=payload.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=payload.get("client_id"),
        client_secret=payload.get("client_secret"),
        scopes=payload.get("scopes"),
    )
    creds.expiry = expiry
    return creds


def get_service(sub: str) -> Resource:
    """Return an authenticated Gmail API resource for the given user sub."""
    payload = load_user_tokens(sub)
    if not payload:
        raise PermissionError("No stored tokens for user")
    creds = _credentials_from_payload(payload)
    if not creds.valid:
        if creds.refresh_token:
            creds.refresh(GoogleRequest())
            payload["access_token"] = creds.token
            if creds.expiry:
                payload["expiry"] = creds.expiry.isoformat()
            save_user_tokens(sub, payload)
        else:
            raise PermissionError("Token expired and no refresh token")
    return build("gmail", "v1", credentials=creds, cache_discovery=False)

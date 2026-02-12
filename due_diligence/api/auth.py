"""API key authentication for the Due Diligence API."""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from due_diligence.api.database import validate_api_key

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def require_api_key(api_key: str | None = Security(api_key_header)) -> dict:
    """Validate the API key from the Authorization header.

    Accepts either:
      - Bearer dd_xxxxx
      - dd_xxxxx
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include 'Authorization: Bearer dd_xxxxx' header.",
        )

    # Strip 'Bearer ' prefix if present
    raw_key = api_key.removeprefix("Bearer ").strip()

    if not raw_key.startswith("dd_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format. Keys start with 'dd_'.",
        )

    key_record = validate_api_key(raw_key)
    if not key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key.",
        )

    return key_record

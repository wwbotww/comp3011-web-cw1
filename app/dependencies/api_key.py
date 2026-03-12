from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import settings
from app.core.security import api_key_matches


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_write_api_key(api_key: Optional[str] = Depends(api_key_header)) -> None:
    if not api_key_matches(api_key or "", settings.write_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )

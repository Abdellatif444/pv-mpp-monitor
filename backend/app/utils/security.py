import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

_security = HTTPBearer(auto_error=True)


def verify_write_access(credentials: HTTPAuthorizationCredentials = Depends(_security)):
    """Bearer token check for write endpoints.

    Requires the Authorization: Bearer <token> header to match API_TOKEN in env.
    """
    token = credentials.credentials if credentials else None
    expected = os.getenv("API_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: API_TOKEN is not set",
        )
    if token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token",
        )
    return True

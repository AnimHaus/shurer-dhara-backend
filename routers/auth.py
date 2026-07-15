from datetime import datetime, timedelta, timezone
import os

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from jose import jwt

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ── helpers ───────────────────────────────────────────────────────────────────

def _get_secret() -> str:
    secret = os.environ.get("JWT_SECRET", "")
    if not secret:
        raise RuntimeError("JWT_SECRET env var is not set")
    return secret


def _create_token(username: str) -> str:
    expire_hours = int(os.environ.get("JWT_EXPIRE_HOURS", "168"))
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=expire_hours),
    }
    return jwt.encode(payload, _get_secret(), algorithm="HS256")


def _verify_credentials(username: str, password: str) -> bool:
    valid_user = os.environ.get("ADMIN_USERNAME", "")
    valid_pass = os.environ.get("ADMIN_PASSWORD", "")
    # Constant-time comparison to avoid timing attacks
    import hmac
    user_ok = hmac.compare_digest(username.encode(), valid_user.encode())
    pass_ok = hmac.compare_digest(password.encode(), valid_pass.encode())
    return user_ok and pass_ok


# ── schemas ───────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── routes ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    if not _verify_credentials(body.username.strip(), body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = _create_token(body.username.strip())
    return TokenResponse(access_token=token)


@router.get("/verify")
def verify(authorization: str | None = None):
    """Lightweight token-check endpoint used by the dashboard middleware."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=["HS256"])
        return {"valid": True, "sub": payload.get("sub")}
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

import os
import secrets
import time

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from db.postgres import get_conn

TOKEN_TTL_SECONDS = 7 * 24 * 3600  # users stay logged in for 7 days

JWT_SECRET = os.environ.get("JWT_SECRET", "")
if not JWT_SECRET:
    # Dev fallback: works, but everyone is logged out whenever the server restarts.
    # In production (Render) set a permanent JWT_SECRET environment variable.
    JWT_SECRET = secrets.token_hex(32)
    print("⚠️  JWT_SECRET not set — using a temporary one. Set JWT_SECRET so logins survive restarts.")

_bearer = HTTPBearer(auto_error=False)

# Used to burn the same time when an email doesn't exist (prevents account probing)
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt()).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), (password_hash or _DUMMY_HASH).encode()) and password_hash is not None
    except ValueError:
        return False


def create_token(user_id: int) -> str:
    now = int(time.time())
    return jwt.encode({"sub": str(user_id), "iat": now, "exp": now + TOKEN_TTL_SECONDS},
                      JWT_SECRET, algorithm="HS256")


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    """FastAPI dependency: returns {"id", "email"} or raises 401."""
    if creds is None:
        raise HTTPException(401, "Not logged in")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Session expired — please log in again")
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(401, "Invalid login — please log in again")

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
    finally:
        conn.close()
    if not row:
        raise HTTPException(401, "Account no longer exists")
    return {"id": row[0], "email": row[1]}
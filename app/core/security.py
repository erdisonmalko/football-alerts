from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db

from app.core.logger import _logger
logger = _logger()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.debug(f"[app.core.security.verify_password] Verifying password for user.")
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    logger.debug(f"[app.core.security.hash_password] Hashing password.")
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    logger.debug(f"[app.core.security.create_access_token] Creating access token for user: {subject}")
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """Returns user_id (sub) or None if token is invalid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        logger.debug(f"[app.core.security.decode_access_token] Decoded access token for user: {payload.get('sub')}")
        return payload.get("sub")
    except JWTError:
        logger.warning(f"[app.core.security.decode_access_token] Failed to decode access token: {token}")
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """FastAPI dependency — returns the authenticated User model or raises 401."""
    from app.services.user_service import get_user_by_id  # avoid circular import
    logger.debug(f"[app.core.security.get_current_user] Getting current user from token.")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(token)
    if not user_id:
        logger.warning(f"[app.core.security.get_current_user] Failed to get current user — invalid token: {token}")
        raise credentials_exception

    user = await get_user_by_id(db, int(user_id))
    if not user or not user.is_active:
        logger.warning(f"[app.core.security.get_current_user] Attempt to access protected resource with inactive user: {user_id}")
        raise credentials_exception
    logger.debug(f"[app.core.security.get_current_user] Successfully authenticated user: {user_id}")
    return user

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import get_logger
from app.core.security import (
    COOKIE_NAME,
    create_access_token,
    get_current_user,
    verify_password,
)
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import UserOut, UserRegister
from app.services.user_service import create_user, get_user_by_email

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Cookie is valid for the same duration as the token
COOKIE_MAX_AGE = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    user = await create_user(db, data)
    await db.commit()
    return user


@router.post("/login", response_model=UserOut)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticates the user and sets an httpOnly cookie with the JWT.
    Returns the user object so the frontend can populate its auth state.
    """
    logger.info(f"Login attempt for email: {form_data.username}")
    user = await get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )

    token = create_access_token(subject=str(user.id))

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,  # JS cannot read this
        secure=settings.is_production,  # HTTPS only in production
        samesite="none" if settings.is_production else "lax",  # cross-origin in prod
    )
    logger.info(f"User logged in successfully: {user.email}")
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    """Clears the auth cookie."""
    response.delete_cookie(key=COOKIE_NAME, samesite="lax")


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    """Returns the currently authenticated user — used by the frontend on load."""
    return current_user

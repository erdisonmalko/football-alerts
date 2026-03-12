from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.schemas.schemas import Token, UserOut, UserRegister
from app.services.user_service import create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])

from app.core.logger import _logger
logger = _logger()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, data.email)
    if existing:
        logger.warning(f"[app.api.routes.register] Registration attempt with existing email: {data.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    user = await create_user(db, data)
    await db.commit()
    logger.info(f"[app.api.routes.register] User registered successfully: {user.email}")
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Standard OAuth2 password flow.
    Send as form-data: username=<email>&password=<password>
    """
    user = await get_user_by_email(db, form_data.username)
    logger.info(f"[app.api.routes.login] Login attempt for email: {form_data.username}")
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"[app.api.routes.login] Failed login attempt for email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        logger.warning(f"[app.api.routes.login] Login attempt for disabled account: {form_data.username}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    token = create_access_token(subject=str(user.id))
    logger.info(f"[app.api.routes.login] User logged in successfully: {form_data.username}")
    return {"access_token": token, "token_type": "bearer"}

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.v1.core.security import get_current_user
from app.v1.db.session import get_db
from app.v1.models.models import User
from app.v1.schemas.schemas import ChallengeAccept, ChallengeCreate, PaginatedChallenges
from fastapi import Query
from app.v1.services import challenge_service, server_service
from app.v1.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["challenges"])


# ── Feed (across all servers) ─────────────────────────────────────────────────


@router.get("/challenges/feed")
async def get_challenge_feed(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await challenge_service.get_user_challenge_feed(db, current_user.id)


# ── Server-scoped challenges ──────────────────────────────────────────────────


@router.post(
    "/servers/{server_id}/challenges",
    status_code=status.HTTP_201_CREATED,
)
async def create_challenge(
    server_id: int,
    data: ChallengeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await server_service.get_membership(db, server_id, current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this server")

    try:
        challenge = await challenge_service.create_challenge(
            db=db,
            server_id=server_id,
            created_by_id=current_user.id,
            match_id=data.match_id,
            stake=data.stake,
            prediction=data.prediction,
            invited_user_ids=data.invited_user_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    return {"id": challenge.id, "status": challenge.status}


@router.get("/servers/{server_id}/challenges", response_model=PaginatedChallenges)
async def list_server_challenges(
    server_id: int,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=5, le=50, description="Results per page"),
    status: Optional[str] = Query(
        default=None, description="Filter by challenge status"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await server_service.get_membership(db, server_id, current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this server")

    items, total = await challenge_service.get_server_challenges(
        db, server_id, current_user.id, page=page, page_size=page_size, status=status
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedChallenges(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/servers/{server_id}/challenges/{challenge_id}")
async def get_challenge(
    server_id: int,
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await server_service.get_membership(db, server_id, current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this server")

    entry = await challenge_service.get_entry(db, challenge_id, current_user.id)
    if not entry:
        raise HTTPException(
            status_code=404, detail="Challenge not found or not invited"
        )

    items, _ = await challenge_service.get_server_challenges(
        db, server_id, current_user.id, page=1, page_size=1000
    )
    match = next((c for c in items if c["id"] == challenge_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Challenge not found")

    return match


@router.post("/servers/{server_id}/challenges/{challenge_id}/accept")
async def accept_challenge(
    server_id: int,
    challenge_id: int,
    data: ChallengeAccept,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await server_service.get_membership(db, server_id, current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this server")

    try:
        entry = await challenge_service.accept_challenge(
            db, challenge_id, current_user.id, data.prediction
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    return {"id": entry.id, "status": entry.status, "prediction": entry.prediction}


@router.post("/servers/{server_id}/challenges/{challenge_id}/decline")
async def decline_challenge(
    server_id: int,
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await server_service.get_membership(db, server_id, current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this server")

    try:
        entry = await challenge_service.decline_challenge(
            db, challenge_id, current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    return {"id": entry.id, "status": entry.status}

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.v1.core.security import get_current_user
from app.v1.db.session import get_db
from app.v1.models.models import User, ServerRole
from app.v1.schemas.schemas import (
    ServerCreate,
    ServerLeaderboard,
    ServerListOut,
    # ServerMemberOut,
    ServerOut,
    ServerUpdate,
)
from app.v1.services import server_service
from app.v1.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/servers", tags=["servers"], redirect_slashes=False)


@router.get("/public", response_model=list[dict])
async def list_public_servers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await server_service.get_public_servers(db, current_user.id)


@router.post("/{server_id}/request-join", status_code=status.HTTP_201_CREATED)
async def request_to_join(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        request = await server_service.request_to_join(db, server_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await db.commit()
    return {"status": "pending", "request_id": request.id}


@router.get("/{server_id}/join-requests")
async def get_join_requests(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await server_service.get_membership(db, server_id, current_user.id)
    if not membership or membership.role != ServerRole.OWNER:
        raise HTTPException(
            status_code=403, detail="Only the owner can view join requests"
        )

    from sqlalchemy import select
    from app.v1.models.models import ServerJoinRequest, JoinRequestStatus

    result = await db.execute(
        select(ServerJoinRequest).where(
            ServerJoinRequest.server_id == server_id,
            ServerJoinRequest.status == JoinRequestStatus.PENDING,
        )
    )
    return result.scalars().all()


@router.post("/{server_id}/join-requests/{request_id}")
async def handle_join_request(
    server_id: int,
    request_id: int,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    accept = payload.get("accept", False)
    try:
        await server_service.handle_join_request(
            db, server_id, request_id, current_user.id, accept
        )
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=403, detail=str(e))
    await db.commit()
    return {"status": "accepted" if accept else "declined"}


# ----------------------------------------------------------------------------


@router.post("/", response_model=ServerOut, status_code=status.HTTP_201_CREATED)
async def create_server(
    data: ServerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    server = await server_service.create_server(
        db, current_user.id, data.name, data.is_public
    )
    await db.commit()
    await db.refresh(server)
    # Return without members — client can fetch full detail separately
    return {
        "id": server.id,
        "name": server.name,
        "invite_code": server.invite_code,
        "created_by_id": server.created_by_id,
        "created_at": server.created_at,
        "members": [],
    }


@router.get("/", response_model=list[ServerListOut])
async def list_my_servers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await server_service.get_user_servers(db, current_user.id)


@router.get("/{server_id}", response_model=ServerOut)
async def get_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await server_service.get_membership(db, server_id, current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this server")

    server = await server_service.get_server(db, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    members = await server_service.get_server_members(db, server_id)
    return {
        "id": server.id,
        "name": server.name,
        "invite_code": server.invite_code,
        "created_by_id": server.created_by_id,
        "created_at": server.created_at,
        "members": members,
    }


@router.patch("/{server_id}", response_model=ServerOut)
async def update_server(
    server_id: int,
    data: ServerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await server_service.get_membership(db, server_id, current_user.id)
    if not membership or membership.role.value != "owner":
        raise HTTPException(
            status_code=403, detail="Only the owner can update the server"
        )

    server = await server_service.get_server(db, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    server.name = data.name
    await db.commit()
    await db.refresh(server)
    return server


@router.post("/join/{invite_code}", response_model=ServerOut)
async def join_by_invite(
    invite_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    server = await server_service.join_server_by_code(db, current_user.id, invite_code)
    if not server:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    await db.commit()
    return server


@router.post("/{server_id}/invite", status_code=status.HTTP_200_OK)
async def invite_by_email(
    server_id: int,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=422, detail="email is required")

    try:
        user = await server_service.invite_member_by_email(
            db, server_id, current_user.id, email
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not user:
        raise HTTPException(status_code=404, detail="No user found with that email")

    await db.commit()
    return {"status": "ok", "user_id": user.id, "email": user.email}


@router.delete("/{server_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    left = await server_service.leave_server(db, server_id, current_user.id)
    if not left:
        raise HTTPException(status_code=404, detail="Not a member of this server")
    await db.commit()


@router.post("/{server_id}/regenerate-invite", status_code=status.HTTP_200_OK)
async def regenerate_invite(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        new_code = await server_service.regenerate_invite_code(
            db, server_id, current_user.id
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    await db.commit()
    return {"invite_code": new_code}


@router.get("/{server_id}/leaderboard", response_model=ServerLeaderboard)
async def get_leaderboard(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await server_service.get_membership(db, server_id, current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this server")

    server = await server_service.get_server(db, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    entries = await server_service.get_leaderboard(db, server_id)
    return {"server_id": server_id, "server_name": server.name, "entries": entries}

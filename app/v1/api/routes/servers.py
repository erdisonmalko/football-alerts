from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.v1.core.security import get_current_user
from app.v1.db.session import get_db
from app.v1.models.models import User, ServerRole, ServerJoinRequest, JoinRequestStatus
from app.v1.schemas.schemas import (
    JoinByCodeIn,
    PaginatedServers,
    PaginatedMyServers,
    ServerCreate,
    ServerLeaderboard,
    ServerDetailOut,
    # ServerPublicOut,
    ServerListOut,
    ServerUpdate,
    ServerUpdateOut,
)
from app.v1.services import server_service
from app.v1.core.logger import get_logger
import math

logger = get_logger(__name__)

router = APIRouter(prefix="/servers", tags=["servers"], redirect_slashes=False)


@router.get("/", response_model=PaginatedServers)
async def list_servers(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=5, le=50, description="Results per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    servers, total = await server_service.get_servers(
        db, current_user.id, page=page, page_size=page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedServers(
        items=servers,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# make this only for public servers
@router.post("/{server_id}/request-join", status_code=status.HTTP_201_CREATED)
async def request_to_join_public(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        request = await server_service.save_request_to_join_public_server(
            db, server_id, current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await db.commit()
    return {"status": "pending", "request_id": request.id}


@router.post("/{server_id}/request-join-by-code", status_code=201)
async def request_to_join_private(
    server_id: int,
    payload: JoinByCodeIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        request = await server_service.request_join_private_by_code(
            db, server_id, current_user.id, payload.invite_code
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    return {"status": "pending", "request_id": request.id}


@router.get("/{server_id}/join-requests/list", status_code=status.HTTP_200_OK)
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

    result = await db.execute(
        select(ServerJoinRequest, User)
        .join(User, User.id == ServerJoinRequest.user_id)
        .where(
            ServerJoinRequest.server_id == server_id,
            ServerJoinRequest.status == JoinRequestStatus.PENDING,
        )
    )
    rows = result.all()

    return [
        {
            "id": req.id,
            "user_id": req.user_id,
            "user_email": user.email,
            "user_full_name": user.full_name or user.email,
            "created_at": req.created_at,
        }
        for req, user in rows
    ]


@router.post("/{server_id}/join-requests/{request_id}")
async def handle_join_request(
    server_id: int,
    request_id: int,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    accept = payload.get("accept", False)
    # convert accept to bool if it's a string
    if isinstance(accept, str):
        accept = accept.lower() == "accept"
    logger.info(
        f"Handling join request {request_id} for server {server_id} from user {current_user.id} - accept: {accept}"
    )
    try:
        await server_service.handle_join_request(
            db, server_id, request_id, current_user.id, bool(accept)
        )
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=403, detail=str(e))
    await db.commit()
    return {"status": "accepted" if accept else "declined"}


# ----------------------------------------------------------------------------


@router.get("/pending-requests-count", status_code=status.HTTP_200_OK)
async def get_pending_requests_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Total pending join requests across all servers the user owns."""
    count = await server_service.get_pending_requests_count(db, current_user.id)
    logger.info(
        f"User {current_user.id} has {count} pending join requests across owned servers"
    )
    return {"count": count}


# ----------------------------------------------------------------------------
@router.post("/", response_model=ServerListOut, status_code=status.HTTP_201_CREATED)
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
        "your_rank": 0,
        "your_points": 0,
        "member_count": 1,  # FIXED
        "is_owner": True,  # FIXED
    }


@router.get("/my-servers", response_model=PaginatedMyServers)
async def list_my_servers(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=15, ge=5, le=50, description="Results per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    servers, total = await server_service.get_user_servers(
        db, current_user.id, page=page, page_size=page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedMyServers(
        items=servers,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{server_id}", response_model=ServerDetailOut)
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
        "invite_code": server.invite_code if membership.role.value == "owner" else None,
        "created_by_id": server.created_by_id,
        "created_at": server.created_at,
        "is_public": server.is_public,
        "is_owner": membership.role.value == "owner",
        "members": members,
    }


@router.patch("/{server_id}", response_model=ServerUpdateOut)
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
    server.is_public = data.is_public

    await db.commit()
    await db.refresh(server, ["members"])  # Refresh to get updated members if needed
    return server


# make this for private servers only
# we maybe need this when will add onboarding users flow
# in case admin wants to invite someone by email and that person is not registered yet,
# we can send them an invite link and when they register with that email,
# they will be added to the server automatically
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


# make this for private servers only
# in case admin wants t udpate the code so that old invite links stop working
@router.post("/{server_id}/regenerate-invite-code", status_code=status.HTTP_200_OK)
async def regenerate_invite_code(
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

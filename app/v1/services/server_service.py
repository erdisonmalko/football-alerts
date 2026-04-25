import datetime
import secrets
import string

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.v1.models.models import (
    InviteStatus,
    Server,
    ServerMember,
    ServerRole,
    User,
    ServerJoinRequest,
    JoinRequestStatus,
)
from app.v1.core.logger import get_logger
from app.v1.services.server_mapper import ServerMapper
from app.v1.services.user_service import get_user_by_email

logger = get_logger(__name__)

_INVITE_ALPHABET = string.ascii_letters + string.digits


def _generate_invite_code(length: int = 10) -> str:
    return "".join(secrets.choice(_INVITE_ALPHABET) for _ in range(length))


async def create_server(
    db: AsyncSession,
    user_id: int,
    name: str,
    is_public: bool = True,
) -> Server:
    code = _generate_invite_code()
    # Ensure uniqueness — extremely unlikely collision but worth checking
    while True:
        existing = await db.execute(select(Server).where(Server.invite_code == code))
        if not existing.scalar_one_or_none():
            break
        code = _generate_invite_code()

    server = Server(
        name=name,
        invite_code=code,
        created_by_id=user_id,
        is_public=is_public,
    )
    db.add(server)
    await db.flush()  # get server.id before adding member

    owner = ServerMember(
        server_id=server.id,
        user_id=user_id,
        role=ServerRole.OWNER,
    )
    db.add(owner)
    await db.flush()

    logger.info(
        "[create_server] user %s created server %s (%s)", user_id, server.id, name
    )
    return server


async def get_server(
    db: AsyncSession,
    server_id: int,
) -> Server | None:
    result = await db.execute(select(Server).where(Server.id == server_id))
    return result.scalar_one_or_none()


async def get_membership(
    db: AsyncSession,
    server_id: int,
    user_id: int,
) -> ServerMember | None:
    result = await db.execute(
        select(ServerMember).where(
            ServerMember.server_id == server_id,
            ServerMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_user_servers(
    db: AsyncSession,
    user_id: int,
) -> list[dict]:
    """
    Returns all servers the user belongs to, with their rank and points.
    """
    memberships = await db.execute(
        select(ServerMember, Server)
        .join(Server, Server.id == ServerMember.server_id)
        .where(ServerMember.user_id == user_id)
        .order_by(Server.created_at.desc())
    )
    rows = memberships.all()

    result = []
    for membership, server in rows:
        dto = await ServerMapper.to_list_out(db, server, membership)
        result.append(dto)
    # for membership, server in rows:
    #     # Count members in server
    #     count_result = await db.execute(
    #         select(func.count())
    #         .select_from(ServerMember)
    #         .where(ServerMember.server_id == server.id)
    #     )
    #     member_count = count_result.scalar_one()

    #     # Compute rank: how many members have more points than this user
    #     rank_result = await db.execute(
    #         select(func.count())
    #         .select_from(ServerMember)
    #         .where(
    #             ServerMember.server_id == server.id,
    #             ServerMember.total_points > membership.total_points,
    #         )
    #     )
    #     rank = rank_result.scalar_one() + 1  # 1-indexed
    #     result.append(
    #         {
    #             "id": server.id,
    #             "name": server.name,
    #             "invite_code": server.invite_code,
    #             "member_count": member_count,
    #             "your_points": membership.total_points,
    #             "your_rank": rank,
    #             "is_owner": (
    #                     membership.role.name == "OWNER"
    #                     if membership and membership.role
    #                     else False
    #                 )
    #         }
    #     )

    return result


async def get_server_members(
    db: AsyncSession,
    server_id: int,
) -> list[dict]:
    """
    Returns members with user details for the server detail view.
    """
    result = await db.execute(
        select(ServerMember, User)
        .join(User, User.id == ServerMember.user_id)
        .where(ServerMember.server_id == server_id)
        .order_by(ServerMember.total_points.desc())
    )
    rows = result.all()

    return [
        {
            "user_id": member.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "role": member.role,
            "joined_at": member.joined_at,
            "total_points": member.total_points,
            "total_wins": member.total_wins,
            "total_losses": member.total_losses,
            "total_draws": member.total_draws,
            "challenge_count": member.challenge_count,
        }
        for member, user in rows
    ]


async def request_join_private_by_code(
    db: AsyncSession,
    server_id: int,
    user_id: int,
    invite_code: str,
) -> ServerJoinRequest:

    # 1. Validate server + code
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.invite_code == invite_code,
            Server.is_public.is_(False),
        )
    )
    server = result.scalar_one_or_none()

    if not server:
        raise ValueError("Invalid invite code")

    # 2. Already member?
    if await get_membership(db, server_id, user_id):
        raise ValueError("Already a member")

    # 3. Existing request?
    result = await db.execute(
        select(ServerJoinRequest).where(
            ServerJoinRequest.server_id == server_id,
            ServerJoinRequest.user_id == user_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        if existing.status == JoinRequestStatus.PENDING:
            raise ValueError("Request already sent")

        if existing.status == JoinRequestStatus.DECLINED:
            raise ValueError("Request was declined")

    # 4. Create request
    request = ServerJoinRequest(
        server_id=server_id,
        user_id=user_id,
    )
    db.add(request)
    await db.flush()

    return request


async def save_request_to_join_public_server(
    db: AsyncSession,
    server_id: int,
    user_id: int,
) -> ServerJoinRequest:

    server_result = await db.execute(
        select(Server).where(Server.id == server_id, Server.is_public.is_(True))
    )
    server = server_result.scalar_one_or_none()
    if not server:
        return None
    # Check Membership
    if await get_membership(db, server_id, user_id):
        raise ValueError("Already a member")

    # Single query for any relevant existing request
    result = await db.execute(
        select(ServerJoinRequest).where(
            ServerJoinRequest.server_id == server_id,
            ServerJoinRequest.user_id == user_id,
            ServerJoinRequest.status.in_(
                [JoinRequestStatus.PENDING, JoinRequestStatus.DECLINED]
            ),
        )
    )
    existing_req = result.scalar_one_or_none()

    # Handle logic based on status
    if existing_req:
        if existing_req.status == JoinRequestStatus.PENDING:
            raise ValueError("Request already sent")

        if existing_req.status == JoinRequestStatus.DECLINED:
            # maybe in the future we count the requests per user and than decide to block them,
            # so we will allow two more requests per user after declined request,
            # if they get all decined by owner, the will not forward more request to join this server
            # for now will just not accept new requests after one declined request
            raise ValueError(
                "Previous request was declined. Please contact the server owner."
            )

    # Create new if none found
    request = ServerJoinRequest(server_id=server_id, user_id=user_id)
    db.add(request)
    await db.flush()
    return request


async def handle_join_request(
    db: AsyncSession,
    server_id: int,
    request_id: int,
    owner_id: int,
    accept: bool,
) -> None:
    membership = await get_membership(db, server_id, owner_id)
    if not membership or membership.role != ServerRole.OWNER:
        raise PermissionError("Only the owner can handle join requests")

    request_result = await db.execute(
        select(ServerJoinRequest).where(
            ServerJoinRequest.id == request_id,
            ServerJoinRequest.server_id == server_id,
        )
    )
    request = request_result.scalar_one_or_none()
    if not request:
        raise ValueError("Join request not found")

    if accept:
        logger.info(
            f"Accepting join request {request_id} for server {server_id} from user {request.user_id}"
        )
        request.status = JoinRequestStatus.ACCEPTED
        member = ServerMember(
            server_id=server_id,
            user_id=request.user_id,
            role=ServerRole.MEMBER,
        )
        db.add(member)
    else:
        logger.info(
            f"Declining join request {request_id} for server {server_id} from user {request.user_id}"
        )
        request.status = JoinRequestStatus.DECLINED

    await db.flush()


async def get_servers(
    db: AsyncSession,
    user_id: int,
) -> list[dict]:
    """All servers — includes membership and request status for the user."""
    result = await db.execute(
        select(Server)
        # .where(Server.is_public.is_(True))
        .order_by(Server.created_at.desc())
    )
    servers = result.scalars().all()

    output = []
    for server in servers:
        count_result = await db.execute(
            select(func.count())
            .select_from(ServerMember)
            .where(ServerMember.server_id == server.id)
        )
        member_count = count_result.scalar_one()
        membership = await get_membership(db, server.id, user_id)

        request_result = await db.execute(
            select(ServerJoinRequest).where(
                ServerJoinRequest.server_id == server.id,
                ServerJoinRequest.user_id == user_id,
                ServerJoinRequest.status == JoinRequestStatus.PENDING,
            )
        )
        pending_request = request_result.scalar_one_or_none()

        output.append(
            {
                "id": server.id,
                "name": server.name,
                "invite_code": server.invite_code,
                "is_public": server.is_public,
                "member_count": member_count,
                "is_member": membership is not None,
                "is_owner": membership.role == ServerRole.OWNER
                if membership
                else False,
                "has_pending_request": pending_request is not None,
            }
        )

    return output


async def get_pending_requests_count(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(func.count())
        .select_from(ServerJoinRequest)
        .join(Server, Server.id == ServerJoinRequest.server_id)
        .join(ServerMember, ServerMember.server_id == Server.id)
        .where(
            ServerJoinRequest.status == JoinRequestStatus.PENDING,
            ServerMember.user_id == user_id,
            ServerMember.role == ServerRole.OWNER,
        )
    )
    return result.scalar_one()


async def invite_member_by_email(
    db: AsyncSession,
    server_id: int,
    requester_id: int,
    email: str,
) -> User | None:
    """
    Owner adds a user by email. Returns the user if found and added,
    None if user doesn't exist.
    Raises PermissionError if requester is not owner.
    """
    membership = await get_membership(db, server_id, requester_id)
    if not membership or membership.role != ServerRole.OWNER:
        raise PermissionError("Only the server owner can invite members")

    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    if not user:
        return None

    existing = await get_membership(db, server_id, user.id)
    if existing:
        return user  # already a member

    new_member = ServerMember(
        server_id=server_id,
        user_id=user.id,
        role=ServerRole.MEMBER,
    )
    db.add(new_member)
    await db.flush()

    logger.info(
        "[invite_member_by_email] user %s added to server %s", user.id, server_id
    )
    return user


async def leave_server(
    db: AsyncSession,
    server_id: int,
    user_id: int,
) -> bool:
    membership = await get_membership(db, server_id, user_id)
    if not membership:
        return False

    if membership.role == ServerRole.OWNER:
        # Transfer ownership to the longest-standing other member
        next_owner_result = await db.execute(
            select(ServerMember)
            .where(
                ServerMember.server_id == server_id,
                ServerMember.user_id != user_id,
            )
            .order_by(ServerMember.joined_at.asc())
            .limit(1)
        )
        next_owner = next_owner_result.scalar_one_or_none()
        if next_owner:
            next_owner.role = ServerRole.OWNER
        else:
            # Last member leaving — delete the server
            server = await get_server(db, server_id)
            if server:
                await db.delete(server)
            return True

    await db.delete(membership)
    await db.flush()

    logger.info("[leave_server] user %s left server %s", user_id, server_id)
    return True


async def regenerate_invite_code(
    db: AsyncSession,
    server_id: int,
    user_id: int,
) -> str:
    membership = await get_membership(db, server_id, user_id)
    if not membership or membership.role != ServerRole.OWNER:
        raise PermissionError("Only the server owner can regenerate the invite code")

    server = await get_server(db, server_id)
    if not server:
        raise ValueError("Server not found")

    new_code = _generate_invite_code()
    server.invite_code = new_code
    await db.flush()

    logger.info("[regenerate_invite_code] server %s new code generated", server_id)
    return new_code


async def get_leaderboard(
    db: AsyncSession,
    server_id: int,
) -> list[dict]:
    result = await db.execute(
        select(ServerMember, User)
        .join(User, User.id == ServerMember.user_id)
        .where(ServerMember.server_id == server_id)
        .order_by(ServerMember.total_points.desc())
    )
    rows = result.all()

    return [
        {
            "rank": idx + 1,
            "user_id": member.user_id,
            "full_name": user.full_name,
            "email": user.email,
            "total_points": member.total_points,
            "total_wins": member.total_wins,
            "total_losses": member.total_losses,
            "total_draws": member.total_draws,
            "challenge_count": member.challenge_count,
        }
        for idx, (member, user) in enumerate(rows)
    ]


# new test routes - not sure
async def get_server_list_out(
    db,
    server_id: int,
    user_id: int,
) -> dict:
    # fetch server
    server_result = await db.execute(select(Server).where(Server.id == server_id))
    server = server_result.scalar_one_or_none()

    if not server:
        return None

    # fetch membership
    membership = await get_membership(db, server_id, user_id)
    if not membership:
        return None

    # member count
    count_result = await db.execute(
        select(func.count())
        .select_from(ServerMember)
        .where(ServerMember.server_id == server_id)
    )
    member_count = count_result.scalar_one()

    # rank
    rank_result = await db.execute(
        select(func.count())
        .select_from(ServerMember)
        .where(
            ServerMember.server_id == server_id,
            ServerMember.total_points > membership.total_points,
        )
    )
    rank = rank_result.scalar_one() + 1

    return {
        "id": server.id,
        "name": server.name,
        "invite_code": server.invite_code,  # optional long-term (you may remove later)
        "member_count": member_count,
        "your_points": membership.total_points,
        "your_rank": rank,
        "is_owner": membership.role == ServerRole.OWNER,
    }

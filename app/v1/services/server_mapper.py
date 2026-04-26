from sqlalchemy import select, func
from app.v1.models.models import (
    ServerJoinRequest,
    ServerMember,
    ServerRole,
    JoinRequestStatus,
)


class ServerMapper:
    @staticmethod
    async def base(db, server):
        count_result = await db.execute(
            select(func.count())
            .select_from(ServerMember)
            .where(ServerMember.server_id == server.id)
        )

        return {
            "id": server.id,
            "name": server.name,
            "is_public": server.is_public,
            "member_count": count_result.scalar_one(),
        }

    @staticmethod
    async def to_discover_out(db, server, user_id):
        base = await ServerMapper.base(db, server)

        from app.v1.services.server_service import get_membership

        membership = await get_membership(db, server.id, user_id)

        request_result = await db.execute(
            select(ServerJoinRequest).where(
                ServerJoinRequest.server_id == server.id,
                ServerJoinRequest.user_id == user_id,
                ServerJoinRequest.status == JoinRequestStatus.PENDING,
            )
        )

        pending = request_result.scalar_one_or_none()

        return {
            **base,
            "is_member": membership is not None,
            "is_owner": membership.role == ServerRole.OWNER if membership else False,
            "invite_code": (
                server.invite_code
                if membership and membership.role == ServerRole.OWNER
                else None
            ),
            "has_pending_request": pending is not None,
        }

    @staticmethod
    async def to_list_out(db, server, membership):
        base = await ServerMapper.base(db, server)

        rank_result = await db.execute(
            select(func.count())
            .select_from(ServerMember)
            .where(
                ServerMember.server_id == server.id,
                ServerMember.total_points > (membership.total_points or 0),
            )
        )

        rank = rank_result.scalar_one() + 1

        return {
            **base,
            "your_points": membership.total_points or 0,
            "your_rank": rank,
            "is_owner": membership.role == ServerRole.OWNER if membership else False,
            "invite_code": (
                server.invite_code
                if membership and membership.role == ServerRole.OWNER
                else None
            ),
        }

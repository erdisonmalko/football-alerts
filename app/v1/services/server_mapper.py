from sqlalchemy import select, func
from app.v1.models.models import ServerMember, ServerRole


class ServerMapper:
    @staticmethod
    async def to_list_out(db, server, membership):
        # member count
        count_result = await db.execute(
            select(func.count())
            .select_from(ServerMember)
            .where(ServerMember.server_id == server.id)
        )
        member_count = count_result.scalar_one()

        # rank
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
            "id": server.id,
            "name": server.name,
            "invite_code": server.invite_code,
            "member_count": member_count,
            "your_points": membership.total_points or 0,
            "your_rank": rank,
            "is_owner": membership.role == ServerRole.OWNER,
        }
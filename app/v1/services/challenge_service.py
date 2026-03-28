import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.v1.models.models import (
    Challenge,
    ChallengeEntry,
    ChallengeEntryResult,
    ChallengeEntryStatus,
    ChallengeStatus,
    Match,
    ServerMember,
    User,
)
from app.v1.core.logger import get_logger

logger = get_logger(__name__)


# ── Scoring ───────────────────────────────────────────────────────────────────
"""
Score prediction handling for challenges.

Frontend sends home_team_id and away_team_id with match data, so users
predict in the format: "HOME_SCORE - AWAY_SCORE" (e.g., "2 - 1")

This approach:
  - Avoids team name parsing issues
  - Validates using match's team IDs on the backend
  - Scores predictions against actual Match.home_score and Match.away_score
  - Supports flexible formatting: "2-1", "2 - 1", "2:1", etc.
"""


def _extract_scoreline(prediction: str) -> tuple[int, int] | None:
    """
    Extracts (home_goals, away_goals) from a score prediction.

    Expected format: "2-1", "2 - 1", "2:1", etc.
    The prediction should only contain the score, not team names.

    Args:
        prediction: A string containing home and away scores separated by -, –, or :

    Returns:
        (home_goals, away_goals) tuple or None if invalid format
    """
    # Match any two numbers separated by -, –, :, or whitespace around them
    match = re.search(r"(\d+)\s*[-–:]\s*(\d+)", prediction)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def validate_prediction(prediction: str) -> bool:
    """
    Validates that a prediction is in the correct score format.

    Args:
        prediction: The prediction string to validate

    Returns:
        True if valid score format, False otherwise
    """
    if not prediction or not isinstance(prediction, str):
        return False
    return _extract_scoreline(prediction.strip()) is not None


def _get_result(home: int, away: int) -> str:
    """Returns 'home', 'away', or 'draw'."""
    if home > away:
        return "home"
    if away > home:
        return "away"
    return "draw"


def score_prediction(
    prediction: str,
    actual_home: int,
    actual_away: int,
) -> int:
    """
    3 points for exact score, 1 point for correct result, 0 for wrong.
    """
    parsed = _extract_scoreline(prediction)
    if parsed is None:
        return 0

    pred_home, pred_away = parsed

    if pred_home == actual_home and pred_away == actual_away:
        return 3

    if _get_result(pred_home, pred_away) == _get_result(actual_home, actual_away):
        return 1

    return 0


# ── Challenge creation ────────────────────────────────────────────────────────


async def create_challenge(
    db: AsyncSession,
    server_id: int,
    created_by_id: int,
    match_id: int,
    stake: str,
    prediction: str,
    invited_user_ids: list[int],
) -> Challenge:
    """
    Creates a challenge and all ChallengeEntry rows.

    Args:
        db: Database session
        server_id: ID of the server where challenge is created
        created_by_id: User ID of challenge creator
        match_id: Match ID (must exist and contain valid team and score info)
        stake: Description of what's at stake (e.g., "Bragging rights")
        prediction: Score prediction in format "HOME_SCORE - AWAY_SCORE" (e.g., "2 - 1")
        invited_user_ids: List of user IDs to invite (empty = all server members)

    Returns:
        The created Challenge object

    Raises:
        ValueError: If match not found, invalid prediction format, or challenge expired
    """
    # Validate prediction format
    if not validate_prediction(prediction):
        raise ValueError(
            f'Invalid prediction format. Expected "HOME_SCORE - AWAY_SCORE" (e.g., "2 - 1"), got: "{prediction}"'
        )

    match_result = await db.execute(select(Match).where(Match.id == match_id))
    match = match_result.scalar_one_or_none()
    if not match:
        raise ValueError("Match not found")

    # Ensure match hasn't already kicked off
    if datetime.now(timezone.utc) >= match.kickoff_utc:
        raise ValueError("Cannot create challenge for a match that has already started")

    challenge = Challenge(
        server_id=server_id,
        match_id=match_id,
        created_by_id=created_by_id,
        stake=stake,
        status=ChallengeStatus.OPEN,
        expires_at=match.kickoff_utc,
    )
    db.add(challenge)
    await db.flush()

    # Creator's entry — auto-accepted
    creator_entry = ChallengeEntry(
        challenge_id=challenge.id,
        user_id=created_by_id,
        prediction=prediction,
        status=ChallengeEntryStatus.ACCEPTED,
        responded_at=datetime.now(timezone.utc),
    )
    db.add(creator_entry)

    # Determine who to invite
    if invited_user_ids:
        invitees = [uid for uid in invited_user_ids if uid != created_by_id]
    else:
        # All server members except creator
        members_result = await db.execute(
            select(ServerMember.user_id).where(
                ServerMember.server_id == server_id,
                ServerMember.user_id != created_by_id,
            )
        )
        invitees = list(members_result.scalars().all())

    for uid in invitees:
        entry = ChallengeEntry(
            challenge_id=challenge.id,
            user_id=uid,
            status=ChallengeEntryStatus.PENDING,
        )
        db.add(entry)

    await db.flush()

    logger.info(
        "[create_challenge] challenge %s created in server %s for match %s with %s invitees",
        challenge.id,
        server_id,
        match_id,
        len(invitees),
    )
    return challenge


# ── Accept / Decline ──────────────────────────────────────────────────────────


async def get_entry(
    db: AsyncSession,
    challenge_id: int,
    user_id: int,
) -> ChallengeEntry | None:
    result = await db.execute(
        select(ChallengeEntry).where(
            ChallengeEntry.challenge_id == challenge_id,
            ChallengeEntry.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def accept_challenge(
    db: AsyncSession,
    challenge_id: int,
    user_id: int,
    prediction: str,
) -> ChallengeEntry:
    """
    Accept a challenge with a score prediction.

    Args:
        db: Database session
        challenge_id: Challenge ID to accept
        user_id: User ID accepting the challenge
        prediction: Score prediction in format "HOME_SCORE - AWAY_SCORE" (e.g., "2 - 1")

    Returns:
        The updated ChallengeEntry

    Raises:
        ValueError: If challenge invalid, user not invited, or prediction format invalid
    """
    # Validate prediction format
    if not validate_prediction(prediction):
        raise ValueError(
            f'Invalid prediction format. Expected "HOME_SCORE - AWAY_SCORE" (e.g., "2 - 1"), got: "{prediction}"'
        )

    challenge_result = await db.execute(
        select(Challenge).where(Challenge.id == challenge_id)
    )
    challenge = challenge_result.scalar_one_or_none()
    if not challenge:
        raise ValueError("Challenge not found")

    if challenge.status != ChallengeStatus.OPEN:
        raise ValueError(f"Challenge is {challenge.status.value}, cannot accept")

    if datetime.now(timezone.utc) >= challenge.expires_at:
        raise ValueError("Challenge has expired — match already kicked off")

    entry = await get_entry(db, challenge_id, user_id)
    if not entry:
        raise ValueError("You were not invited to this challenge")

    if entry.status == ChallengeEntryStatus.ACCEPTED:
        raise ValueError("You have already accepted this challenge")

    if entry.status == ChallengeEntryStatus.DECLINED:
        raise ValueError("You already declined this challenge")

    entry.prediction = prediction
    entry.status = ChallengeEntryStatus.ACCEPTED
    entry.responded_at = datetime.now(timezone.utc)
    await db.flush()

    logger.info(
        "[accept_challenge] user %s accepted challenge %s with prediction %s",
        user_id,
        challenge_id,
        prediction,
    )
    return entry


async def decline_challenge(
    db: AsyncSession,
    challenge_id: int,
    user_id: int,
) -> ChallengeEntry:
    challenge_result = await db.execute(
        select(Challenge).where(Challenge.id == challenge_id)
    )
    challenge = challenge_result.scalar_one_or_none()
    if not challenge:
        raise ValueError("Challenge not found")

    if challenge.status != ChallengeStatus.OPEN:
        raise ValueError(f"Challenge is {challenge.status.value}, cannot decline")

    entry = await get_entry(db, challenge_id, user_id)
    if not entry:
        raise ValueError("You were not invited to this challenge")

    if entry.status != ChallengeEntryStatus.PENDING:
        raise ValueError("You have already responded to this challenge")

    entry.status = ChallengeEntryStatus.DECLINED
    entry.responded_at = datetime.now(timezone.utc)
    await db.flush()

    logger.info(
        "[decline_challenge] user %s declined challenge %s", user_id, challenge_id
    )
    return entry


# ── Settlement ────────────────────────────────────────────────────────────────


async def settle_challenge(
    db: AsyncSession,
    challenge: Challenge,
) -> None:
    """
    Scores all accepted entries, assigns win/loss/draw,
    updates ServerMember lifetime stats.
    """
    match_result = await db.execute(select(Match).where(Match.id == challenge.match_id))
    match = match_result.scalar_one_or_none()

    if not match or match.home_score is None or match.away_score is None:
        logger.warning(
            "[settle_challenge] match %s has no score yet", challenge.match_id
        )
        return

    entries_result = await db.execute(
        select(ChallengeEntry).where(
            ChallengeEntry.challenge_id == challenge.id,
            ChallengeEntry.status == ChallengeEntryStatus.ACCEPTED,
        )
    )
    entries = list(entries_result.scalars().all())

    if not entries:
        challenge.status = ChallengeStatus.SETTLED
        challenge.settled_at = datetime.now(timezone.utc)
        return

    # Score everyone
    for entry in entries:
        entry.points_earned = score_prediction(
            entry.prediction or "",
            match.home_score,
            match.away_score,
        )

    # Determine win/loss/draw
    max_points = max(e.points_earned for e in entries)

    for entry in entries:
        if entry.points_earned == max_points and max_points > 0:
            # Check if it's a shared top spot
            top_count = sum(1 for e in entries if e.points_earned == max_points)
            entry.result = (
                ChallengeEntryResult.DRAW if top_count > 1 else ChallengeEntryResult.WIN
            )
        elif max_points == 0:
            # Everyone got 0 — everyone draws
            entry.result = ChallengeEntryResult.DRAW
        else:
            entry.result = ChallengeEntryResult.LOSS

    # Update ServerMember stats
    for entry in entries:
        member_result = await db.execute(
            select(ServerMember).where(
                ServerMember.server_id == challenge.server_id,
                ServerMember.user_id == entry.user_id,
            )
        )
        member = member_result.scalar_one_or_none()
        if not member:
            continue

        member.total_points += entry.points_earned
        member.challenge_count += 1

        if entry.result == ChallengeEntryResult.WIN:
            member.total_wins += 1
        elif entry.result == ChallengeEntryResult.LOSS:
            member.total_losses += 1
        elif entry.result == ChallengeEntryResult.DRAW:
            member.total_draws += 1

    challenge.status = ChallengeStatus.SETTLED
    challenge.settled_at = datetime.now(timezone.utc)
    await db.flush()

    logger.info(
        "[settle_challenge] challenge %s settled — %s entries scored",
        challenge.id,
        len(entries),
    )


async def void_challenge(
    db: AsyncSession,
    challenge: Challenge,
) -> None:
    """
    Voids all entries and the challenge itself.
    Called when match is postponed/cancelled.
    """
    entries_result = await db.execute(
        select(ChallengeEntry).where(ChallengeEntry.challenge_id == challenge.id)
    )
    for entry in entries_result.scalars().all():
        entry.status = ChallengeEntryStatus.VOID

    challenge.status = ChallengeStatus.VOID
    await db.flush()

    logger.info("[void_challenge] challenge %s voided", challenge.id)


# ── Lock expired challenges ───────────────────────────────────────────────────


async def lock_expired_challenges(db: AsyncSession) -> int:
    """
    Moves OPEN challenges past their expires_at to LOCKED.
    Called by Celery every 15 minutes.
    """
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Challenge).where(
            Challenge.status == ChallengeStatus.OPEN,
            Challenge.expires_at <= now,
        )
    )
    challenges = result.scalars().all()

    for challenge in challenges:
        challenge.status = ChallengeStatus.LOCKED

    await db.flush()

    if challenges:
        logger.info("[lock_expired_challenges] locked %s challenges", len(challenges))

    return len(challenges)


async def find_challenges_to_settle(db: AsyncSession) -> list[Challenge]:
    """
    Returns LOCKED challenges where the match is FINISHED.
    """
    result = await db.execute(
        select(Challenge)
        .join(Match, Match.id == Challenge.match_id)
        .where(
            Challenge.status == ChallengeStatus.LOCKED,
            Match.status == "FINISHED",
        )
    )
    return list(result.scalars().all())


async def find_challenges_to_void(db: AsyncSession) -> list[Challenge]:
    """
    Returns OPEN or LOCKED challenges where the match is POSTPONED or CANCELLED.
    """
    result = await db.execute(
        select(Challenge)
        .join(Match, Match.id == Challenge.match_id)
        .where(
            Challenge.status.in_([ChallengeStatus.OPEN, ChallengeStatus.LOCKED]),
            Match.status.in_(["POSTPONED", "CANCELLED"]),
        )
    )
    return list(result.scalars().all())


# ── Feed queries ──────────────────────────────────────────────────────────────


async def get_user_challenge_feed(
    db: AsyncSession,
    user_id: int,
) -> dict:
    """
    Returns all challenges for a user across all servers,
    grouped into incoming / active / sent / history.
    """
    entries_result = await db.execute(
        select(ChallengeEntry, Challenge, Match)
        .join(Challenge, Challenge.id == ChallengeEntry.challenge_id)
        .join(Match, Match.id == Challenge.match_id)
        .where(ChallengeEntry.user_id == user_id)
        .order_by(Challenge.created_at.desc())
    )
    rows = entries_result.all()

    incoming = []
    active = []
    sent = []
    history = []

    for entry, challenge, match in rows:
        item = _build_challenge_item(challenge, match, entry)

        if challenge.status in (ChallengeStatus.SETTLED, ChallengeStatus.VOID):
            history.append(item)
        elif (
            entry.status == ChallengeEntryStatus.PENDING
            and challenge.created_by_id != user_id
        ):
            incoming.append(item)
        elif entry.status == ChallengeEntryStatus.ACCEPTED and challenge.status in (
            ChallengeStatus.OPEN,
            ChallengeStatus.LOCKED,
        ):
            active.append(item)
        elif (
            challenge.created_by_id == user_id
            and challenge.status == ChallengeStatus.OPEN
        ):
            sent.append(item)
        else:
            history.append(item)

    return {
        "incoming": incoming,
        "active": active,
        "sent": sent,
        "history": history,
    }


async def get_server_challenges(
    db: AsyncSession,
    server_id: int,
) -> list[dict]:
    result = await db.execute(
        select(Challenge, Match)
        .join(Match, Match.id == Challenge.match_id)
        .where(Challenge.server_id == server_id)
        .order_by(Challenge.created_at.desc())
    )
    rows = result.all()

    challenges = []
    for challenge, match in rows:
        entries_result = await db.execute(
            select(ChallengeEntry, User)
            .join(User, User.id == ChallengeEntry.user_id)
            .where(ChallengeEntry.challenge_id == challenge.id)
        )
        entry_rows = entries_result.all()

        item = _build_challenge_item(challenge, match)
        item["entries"] = [
            {
                "id": entry.id,
                "user_id": entry.user_id,
                "email": user.email,
                "full_name": user.full_name,
                "prediction": entry.prediction,
                "status": entry.status,
                "points_earned": entry.points_earned,
                "result": entry.result,
                "responded_at": entry.responded_at,
            }
            for entry, user in entry_rows
        ]
        challenges.append(item)

    return challenges


def _build_challenge_item(
    challenge: Challenge,
    match: Match,
    my_entry: Optional[ChallengeEntry] = None,
) -> dict:
    return {
        "id": challenge.id,
        "server_id": challenge.server_id,
        "match_id": challenge.match_id,
        "created_by_id": challenge.created_by_id,
        "stake": challenge.stake,
        "status": challenge.status,
        "expires_at": challenge.expires_at,
        "settled_at": challenge.settled_at,
        "created_at": challenge.created_at,
        "my_entry": {
            "id": my_entry.id,
            "prediction": my_entry.prediction,
            "status": my_entry.status,
            "points_earned": my_entry.points_earned,
            "result": my_entry.result,
        }
        if my_entry
        else None,
        "match": {
            "id": match.id,
            "home_team_name": match.home_team_name,
            "away_team_name": match.away_team_name,
            "kickoff_utc": match.kickoff_utc,
            "league_code": match.league_code,
            "league_name": match.league_name,
            "status": match.status,
            "home_score": match.home_score,
            "away_score": match.away_score,
        },
    }

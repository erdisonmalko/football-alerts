#!/usr/bin/env python3
"""
Football Alerts — Database Seed Script
=======================================
Populates the database with realistic test data for load testing and UI validation.

Usage:
    python seed_db.py --db-url postgresql://user:pass@localhost:5432/football_alerts
    python seed_db.py --db-url postgresql://... --dry-run
    python seed_db.py --db-url postgresql://... --clean   # removes all seed_ data first
    python seed_db.py --db-url postgresql://... --users 500 --servers 25

Seed prefix: all seeded users have email prefix seed_user_ for easy cleanup.
"""

import argparse
import asyncio
import random
import secrets
import string
import sys
from datetime import datetime, timedelta, timezone

import bcrypt
from faker import Faker
from sqlalchemy import text, func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

fake = Faker("en_GB")
Faker.seed(42)
random.seed(42)

SEED_PREFIX = "seed_user_"
SEED_PASSWORD_HASH = bcrypt.hashpw(b"SeedPass123", bcrypt.gensalt()).decode()

# ── Realistic football data ────────────────────────────────────────────────────

LEAGUES = [
    ("PL", "Premier League", "England"),
    ("PD", "La Liga", "Spain"),
    ("SA", "Serie A", "Italy"),
    ("BL1", "Bundesliga", "Germany"),
    ("FL1", "Ligue 1", "France"),
    ("CL", "Champions League", "Europe"),
    ("PPL", "Primeira Liga", "Portugal"),
    ("DED", "Eredivisie", "Netherlands"),
]

TEAMS = [
    (57, "Arsenal FC", "PL"),
    (61, "Chelsea FC", "PL"),
    (65, "Manchester City FC", "PL"),
    (66, "Manchester United FC", "PL"),
    (73, "Tottenham Hotspur FC", "PL"),
    (86, "Real Madrid CF", "PD"),
    (81, "FC Barcelona", "PD"),
    (78, "Atletico de Madrid", "PD"),
    (108, "FC Bayern München", "BL1"),
    (5, "FC Bayern München", "BL1"),
    (98, "AC Milan", "SA"),
    (109, "Juventus FC", "SA"),
    (99, "Inter Milan", "SA"),
    (524, "Paris Saint-Germain", "FL1"),
    (503, "SL Benfica", "PPL"),
    (503, "FC Porto", "PPL"),
]

STAKES = [
    "Buy me a beer 🍺",
    "Loser buys dinner 🍕",
    "50 pushups 💪",
    "Bragging rights only 🏆",
    "Loser does dishes for a week",
    "Winner picks the next match to watch",
    "Loser buys coffee ☕",
    "100 burpees 😅",
    "Loser washes the car 🚗",
    "Loser pays for the next takeaway",
    "Winner chooses the next series to watch",
    "Eternal glory and respect 🎖️",
]

SERVER_NAMES = [
    "The Lads FC",
    "Sunday League Boys",
    "Office Banter United",
    "Premier League Predictions",
    "Champions League Club",
    "The Tactical Analysts",
    "Weekend Warriors",
    "Pub Quiz Predictors",
    "Sofa Managers FC",
    "The Armchair Experts",
    "Fantasy Football Legends",
    "Bootroom Boys",
    "The Gaffer's Inner Circle",
    "Match Day Maniacs",
    "Second Season Syndrome",
    "Tiki-Taka Believers",
    "Park the Bus FC",
    "Gegenpressing Giants",
    "The High Line",
    "Total Football Club",
    "Wonderkids United",
    "Transfer Window Addicts",
    "VAR Victims United",
    "The Offside Trap",
    "Extra Time FC",
    "Penalty Shootout Kings",
    "Hat-trick Heroes",
    "Bicycle Kick Believers",
    "Chip Shot Champions",
    "The Nutmeg Collective",
    "Backheel Brigade",
    "Rabona Rebels",
    "Wondergoal Watchers",
    "Set Piece Specialists",
    "Counter Attack Kings",
    "The Deep Block",
    "Overlap Overlords",
    "Through Ball Theologians",
    "One Touch FC",
    "Dummy Run Disciples",
    "Wall Pass Warriors",
    "The Overlap Artists",
    "Sweeper Keepers",
    "Box-to-Box Brigade",
    "False Nine Fellowship",
    "Inverted Wingers Inc",
    "Shadow Striker Society",
    "Deep Lying Playmakers",
    "Advanced Playmakers FC",
    "The Ball Winners",
]


# ── Helpers ────────────────────────────────────────────────────────────────────


def _invite_code(length: int = 10) -> str:
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(length)
    )


def _score() -> tuple[int, int]:
    return random.randint(0, 5), random.randint(0, 5)


def _prediction() -> str:
    return f"{random.randint(0, 4)}-{random.randint(0, 4)}"


def _past_dt(days_back: int = 30) -> datetime:
    return datetime.now(timezone.utc) - timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
    )


def _future_dt(days_ahead: int = 14) -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        days=random.randint(1, days_ahead),
        hours=random.randint(0, 23),
    )


# ── Core seeding functions ─────────────────────────────────────────────────────


async def seed_users(db: AsyncSession, count: int) -> list[int]:
    """Create seed users, return their IDs."""
    print(f"  → Creating {count} users...")
    user_ids = []
    batch = []

    for i in range(count):
        first = fake.first_name()
        last = fake.last_name()
        email = f"{SEED_PREFIX}{i:04d}_{first.lower()}_{last.lower()}@example.com"
        batch.append(
            {
                "email": email,
                "hashed_password": SEED_PASSWORD_HASH,
                "full_name": f"{first} {last}",
                "is_active": True,
                "is_verified": random.random() > 0.2,
            }
        )

        if len(batch) >= 100:
            # Build multi-row INSERT statement
            placeholders = []
            params = {}
            for idx, item in enumerate(batch):
                placeholders.append(
                    f"(:email_{idx}, :hashed_password_{idx}, :full_name_{idx}, :is_active_{idx}, :is_verified_{idx})"
                )
                params[f"email_{idx}"] = item["email"]
                params[f"hashed_password_{idx}"] = item["hashed_password"]
                params[f"full_name_{idx}"] = item["full_name"]
                params[f"is_active_{idx}"] = item["is_active"]
                params[f"is_verified_{idx}"] = item["is_verified"]

            query = f"""
                INSERT INTO users (email, hashed_password, full_name, is_active, is_verified)
                VALUES {",".join(placeholders)}
                ON CONFLICT (email) DO NOTHING
                RETURNING id
            """
            result = await db.execute(text(query), params)
            user_ids.extend(r[0] for r in result.fetchall())
            batch = []

    if batch:
        # Handle remaining batch
        placeholders = []
        params = {}
        for idx, item in enumerate(batch):
            placeholders.append(
                f"(:email_{idx}, :hashed_password_{idx}, :full_name_{idx}, :is_active_{idx}, :is_verified_{idx})"
            )
            params[f"email_{idx}"] = item["email"]
            params[f"hashed_password_{idx}"] = item["hashed_password"]
            params[f"full_name_{idx}"] = item["full_name"]
            params[f"is_active_{idx}"] = item["is_active"]
            params[f"is_verified_{idx}"] = item["is_verified"]

        query = f"""
            INSERT INTO users (email, hashed_password, full_name, is_active, is_verified)
            VALUES {",".join(placeholders)}
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        """
        result = await db.execute(text(query), params)
        user_ids.extend(r[0] for r in result.fetchall())

    await db.flush()
    print(f"     ✓ {len(user_ids)} users created")
    return user_ids


async def seed_subscriptions(
    db: AsyncSession, user_ids: list[int], match_ids: list[int]
) -> int:
    """Give each user 1-5 subscriptions spread across leagues, teams, matches."""
    print(f"  → Creating subscriptions for {len(user_ids)} users...")
    count = 0

    for user_id in user_ids:
        n_subs = random.randint(1, 5)
        sub_types = random.choices(
            ["league", "team", "match"], weights=[0.4, 0.4, 0.2], k=n_subs
        )
        seen = set()

        for sub_type in sub_types:
            if sub_type == "league":
                league = random.choice(LEAGUES)
                key = ("league", league[0])
                if key in seen:
                    continue
                seen.add(key)
                await db.execute(
                    text("""
                    INSERT INTO subscriptions (user_id, subscription_type, external_id, display_name)
                    VALUES (:uid, 'league', :ext_id, :name)
                    ON CONFLICT (user_id, subscription_type, external_id) DO NOTHING
                """),
                    {"uid": user_id, "ext_id": league[0], "name": league[1]},
                )
                count += 1

            elif sub_type == "team":
                team = random.choice(TEAMS)
                key = ("team", str(team[0]))
                if key in seen:
                    continue
                seen.add(key)
                await db.execute(
                    text("""
                    INSERT INTO subscriptions (user_id, subscription_type, external_id, display_name)
                    VALUES (:uid, 'team', :ext_id, :name)
                    ON CONFLICT (user_id, subscription_type, external_id) DO NOTHING
                """),
                    {"uid": user_id, "ext_id": str(team[0]), "name": team[1]},
                )
                count += 1

            elif sub_type == "match" and match_ids:
                match_id = random.choice(match_ids)
                key = ("match", str(match_id))
                if key in seen:
                    continue
                seen.add(key)
                await db.execute(
                    text("""
                    INSERT INTO subscriptions (user_id, subscription_type, external_id, display_name)
                    VALUES (:uid, 'match', :ext_id, :name)
                    ON CONFLICT (user_id, subscription_type, external_id) DO NOTHING
                """),
                    {"uid": user_id, "ext_id": str(match_id), "name": "Match Alert"},
                )
                count += 1

    await db.flush()
    print(f"     ✓ {count} subscriptions created")
    return count


async def seed_google_tokens(db: AsyncSession, user_ids: list[int]) -> int:
    """Give ~15% of users a fake Google token."""
    token_users = random.sample(user_ids, max(1, len(user_ids) // 7))
    count = 0
    for user_id in token_users:
        expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        await db.execute(
            text("""
            INSERT INTO google_tokens (user_id, access_token, refresh_token, token_expiry)
            VALUES (:uid, :access, :refresh, :expiry)
            ON CONFLICT (user_id) DO NOTHING
        """),
            {
                "uid": user_id,
                "access": f"ya29.seed_access_{secrets.token_hex(16)}",
                "refresh": f"1//seed_refresh_{secrets.token_hex(16)}",
                "expiry": expiry,
            },
        )
        count += 1
    await db.flush()
    print(f"     ✓ {count} Google tokens created")
    return count


async def seed_alert_logs(
    db: AsyncSession, user_ids: list[int], match_ids: list[int]
) -> int:
    """Create realistic alert log history."""
    if not match_ids:
        print("     ⚠ No matches found — skipping alert logs")
        return 0

    print(f"  → Creating alert logs...")
    count = 0
    alert_types = ["1_week", "3_days", "6_hours"]
    sample_users = random.sample(user_ids, min(200, len(user_ids)))
    sample_matches = random.sample(match_ids, min(20, len(match_ids)))

    for user_id in sample_users:
        for match_id in random.sample(
            sample_matches, random.randint(1, min(3, len(sample_matches)))
        ):
            alert_type = random.choice(alert_types)
            try:
                await db.execute(
                    text("""
                    INSERT INTO alert_logs (user_id, match_id, alert_type, sent_at)
                    VALUES (:uid, :mid, :atype, :sent_at)
                    ON CONFLICT (user_id, match_id, alert_type) DO NOTHING
                """),
                    {
                        "uid": user_id,
                        "mid": match_id,
                        "atype": alert_type,
                        "sent_at": _past_dt(7),
                    },
                )
                count += 1
            except Exception:
                pass

    await db.flush()
    print(f"     ✓ {count} alert logs created")
    return count


async def seed_servers(
    db: AsyncSession,
    user_ids: list[int],
    match_ids: list[int],
    server_count: int,
) -> int:
    """Create servers with members, join requests, and challenges."""
    print(f"  → Creating {server_count} servers...")

    names = random.sample(SERVER_NAMES, min(server_count, len(SERVER_NAMES)))
    if server_count > len(names):
        extras = [f"Server {i}" for i in range(server_count - len(names))]
        names += extras

    total_challenges = 0
    total_join_requests = 0

    for i, name in enumerate(names):
        is_public = random.random() > 0.35  # 65% public

        # Create server
        result = await db.execute(
            text("""
            INSERT INTO servers (name, invite_code, created_by_id, is_public)
            VALUES (:name, :code, :owner_id, :is_public)
            RETURNING id
        """),
            {
                "name": name,
                "code": _invite_code(),
                "owner_id": random.choice(user_ids),
                "is_public": is_public,
            },
        )
        server_id = result.scalar_one()

        # Owner membership — get the owner id
        owner_result = await db.execute(
            text("SELECT created_by_id FROM servers WHERE id = :sid"),
            {"sid": server_id},
        )
        owner_id = owner_result.scalar_one()

        await db.execute(
            text("""
            INSERT INTO server_members (server_id, user_id, role, total_points, total_wins, total_losses, total_draws, challenge_count)
            VALUES (:sid, :uid, 'owner', :pts, :wins, :losses, :draws, :cc)
            ON CONFLICT (server_id, user_id) DO NOTHING
        """),
            {
                "sid": server_id,
                "uid": owner_id,
                "pts": random.randint(0, 30),
                "wins": random.randint(0, 10),
                "losses": random.randint(0, 10),
                "draws": random.randint(0, 5),
                "cc": random.randint(0, 15),
            },
        )

        # Add 2-20 members
        n_members = random.randint(2, 20)
        member_pool = [uid for uid in user_ids if uid != owner_id]
        members = random.sample(member_pool, min(n_members, len(member_pool)))

        for user_id in members:
            await db.execute(
                text("""
                INSERT INTO server_members (server_id, user_id, role, total_points, total_wins, total_losses, total_draws, challenge_count)
                VALUES (:sid, :uid, 'member', :pts, :wins, :losses, :draws, :cc)
                ON CONFLICT (server_id, user_id) DO NOTHING
            """),
                {
                    "sid": server_id,
                    "uid": user_id,
                    "pts": random.randint(0, 25),
                    "wins": random.randint(0, 8),
                    "losses": random.randint(0, 8),
                    "draws": random.randint(0, 4),
                    "cc": random.randint(0, 12),
                },
            )

        # Join requests for private servers
        if not is_public:
            requesters = random.sample(
                [uid for uid in user_ids if uid not in members and uid != owner_id],
                min(random.randint(1, 8), len(user_ids) - len(members) - 1),
            )
            for requester_id in requesters:
                status = random.choice(["pending", "pending", "accepted", "declined"])
                try:
                    await db.execute(
                        text("""
                        INSERT INTO server_join_requests (server_id, user_id, status)
                        VALUES (:sid, :uid, :status)
                        ON CONFLICT (server_id, user_id) DO NOTHING
                    """),
                        {"sid": server_id, "uid": requester_id, "status": status},
                    )
                    total_join_requests += 1
                except Exception:
                    pass

        # Create challenges for this server
        if match_ids:
            all_server_members = [owner_id] + members
            n_challenges = random.randint(2, 10)

            for _ in range(n_challenges):
                match_id = random.choice(match_ids)
                creator_id = random.choice(all_server_members)
                challenge_status = random.choice(
                    ["open", "open", "locked", "settled", "settled", "void"]
                )

                # Set realistic timestamps
                if challenge_status == "settled":
                    expires_at = _past_dt(14)
                    settled_at = expires_at + timedelta(hours=random.randint(2, 4))
                elif challenge_status == "locked":
                    expires_at = _past_dt(2)
                    settled_at = None
                elif challenge_status == "void":
                    expires_at = _past_dt(7)
                    settled_at = None
                else:  # open
                    expires_at = _future_dt(14)
                    settled_at = None

                ch_result = await db.execute(
                    text("""
                    INSERT INTO challenges (server_id, match_id, created_by_id, stake, status, expires_at, settled_at)
                    VALUES (:sid, :mid, :creator, :stake, :status, :expires_at, :settled_at)
                    RETURNING id
                """),
                    {
                        "sid": server_id,
                        "mid": match_id,
                        "creator": creator_id,
                        "stake": random.choice(STAKES),
                        "status": challenge_status,
                        "expires_at": expires_at,
                        "settled_at": settled_at,
                    },
                )
                challenge_id = ch_result.scalar_one()
                total_challenges += 1

                # Creator entry — always accepted
                creator_pred = _prediction()
                await db.execute(
                    text("""
                    INSERT INTO challenge_entries (challenge_id, user_id, prediction, status, points_earned, result, responded_at)
                    VALUES (:cid, :uid, :pred, 'accepted', :pts, :result, :responded_at)
                    ON CONFLICT (challenge_id, user_id) DO NOTHING
                """),
                    {
                        "cid": challenge_id,
                        "uid": creator_id,
                        "pred": creator_pred,
                        "pts": random.randint(0, 3)
                        if challenge_status == "settled"
                        else 0,
                        "result": random.choice(["win", "loss", "draw"])
                        if challenge_status == "settled"
                        else None,
                        "responded_at": _past_dt(20),
                    },
                )

                # Other members' entries
                invitees = [m for m in all_server_members if m != creator_id]
                n_invitees = random.randint(1, min(len(invitees), 8))

                for invitee_id in random.sample(invitees, n_invitees):
                    if challenge_status == "open":
                        entry_status = random.choice(
                            ["pending", "pending", "accepted", "declined"]
                        )
                    elif challenge_status == "locked":
                        entry_status = random.choice(
                            ["accepted", "accepted", "declined", "pending"]
                        )
                    elif challenge_status == "settled":
                        entry_status = random.choice(
                            ["accepted", "accepted", "declined"]
                        )
                    else:  # void
                        entry_status = "void"

                    prediction = _prediction() if entry_status == "accepted" else None
                    points = (
                        random.randint(0, 3)
                        if (
                            challenge_status == "settled" and entry_status == "accepted"
                        )
                        else 0
                    )
                    result = (
                        random.choice(["win", "loss", "draw"])
                        if (
                            challenge_status == "settled" and entry_status == "accepted"
                        )
                        else None
                    )
                    responded_at = _past_dt(18) if entry_status != "pending" else None

                    try:
                        await db.execute(
                            text("""
                            INSERT INTO challenge_entries (challenge_id, user_id, prediction, status, points_earned, result, responded_at)
                            VALUES (:cid, :uid, :pred, :status, :pts, :result, :responded_at)
                            ON CONFLICT (challenge_id, user_id) DO NOTHING
                        """),
                            {
                                "cid": challenge_id,
                                "uid": invitee_id,
                                "pred": prediction,
                                "status": entry_status,
                                "pts": points,
                                "result": result,
                                "responded_at": responded_at,
                            },
                        )
                    except Exception:
                        pass

        if (i + 1) % 10 == 0:
            print(f"     ... {i + 1}/{server_count} servers done")

    await db.flush()
    print(
        f"     ✓ {server_count} servers, {total_challenges} challenges, {total_join_requests} join requests created"
    )
    return server_count


async def clean_seed_data(db: AsyncSession) -> None:
    """Remove all seed data by prefix."""
    print("  → Cleaning existing seed data...")

    result = await db.execute(
        text("SELECT id FROM users WHERE email LIKE :prefix"),
        {"prefix": f"{SEED_PREFIX}%"},
    )
    seed_user_ids = [r[0] for r in result.fetchall()]

    if not seed_user_ids:
        print("     ✓ No seed data found")
        return

    # CASCADE deletes handle subscriptions, alert_logs, server_members, etc.
    await db.execute(
        text("DELETE FROM users WHERE email LIKE :prefix"),
        {"prefix": f"{SEED_PREFIX}%"},
    )

    # Clean up orphaned servers created by seed users
    await db.execute(
        text("""
        DELETE FROM servers
        WHERE created_by_id NOT IN (SELECT id FROM users)
    """)
    )

    await db.flush()
    print(f"     ✓ Removed {len(seed_user_ids)} seed users and all related data")


async def count_existing_seed(db: AsyncSession) -> int:
    result = await db.execute(
        text("SELECT COUNT(*) FROM users WHERE email LIKE :prefix"),
        {"prefix": f"{SEED_PREFIX}%"},
    )
    return result.scalar_one()


async def get_match_ids(db: AsyncSession) -> list[int]:
    result = await db.execute(text("SELECT id FROM matches LIMIT 100"))
    return [r[0] for r in result.fetchall()]


async def print_summary(db: AsyncSession) -> None:
    """Print a summary of what's in the database."""
    tables = [
        ("users", "Users"),
        ("subscriptions", "Subscriptions"),
        ("servers", "Servers"),
        ("server_members", "Server Members"),
        ("server_join_requests", "Join Requests"),
        ("challenges", "Challenges"),
        ("challenge_entries", "Challenge Entries"),
        ("alert_logs", "Alert Logs"),
        ("google_tokens", "Google Tokens"),
        ("matches", "Matches (existing)"),
    ]
    print("\n  Database summary:")
    for table, label in tables:
        try:
            result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar_one()
            print(f"     {label:<25} {count:>6,}")
        except Exception:
            pass


# ── Main ───────────────────────────────────────────────────────────────────────


async def main(args: argparse.Namespace) -> None:
    db_url = args.db_url

    # Convert sync postgres:// to async postgresql+asyncpg://
    if db_url.startswith("postgresql://") or db_url.startswith("postgres://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

    print(f"\n🌱 Football Alerts Seed Script")
    print(f"   Target: {db_url.split('@')[-1]}")  # hide credentials
    print(f"   Users:  {args.users}")
    print(f"   Servers: {args.servers}")
    print(f"   Mode:   {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"   Clean:  {args.clean}\n")

    engine = create_async_engine(db_url, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        # Check existing seed data
        existing = await count_existing_seed(db)
        if existing > 0 and not args.clean and not args.force:
            print(f"  ⚠  Found {existing} existing seed users.")
            print(f"     Use --clean to remove them first, or --force to add more.\n")
            await engine.dispose()
            return

        if args.dry_run:
            print("  DRY RUN — showing what would be created:\n")
            match_ids = await get_match_ids(db)
            print(f"  Would create:")
            print(f"     {args.users:>6,} users (prefix: {SEED_PREFIX})")
            print(f"     ~{args.users * 3:>5,} subscriptions (~3 per user)")
            print(
                f"     {args.servers:>6,} servers ({int(args.servers * 0.65)} public, {int(args.servers * 0.35)} private)"
            )
            print(f"     ~{args.servers * 10:>5,} server members")
            print(f"     ~{args.servers * 5:>5,} challenges")
            print(f"     ~{args.servers * 25:>5,} challenge entries")
            print(f"     ~{args.users // 7:>5,} Google tokens")
            print(f"     {len(match_ids):>6,} matches available to reference")
            await print_summary(db)
            await engine.dispose()
            return

        # Clean first if requested
        if args.clean:
            await clean_seed_data(db)
            await db.commit()

        print("  Starting seed...\n")
        t_start = datetime.now()

        # 1. Users
        user_ids = await seed_users(db, args.users)
        await db.commit()

        # 2. Match IDs (already in DB from football-data.org sync)
        match_ids = await get_match_ids(db)
        if not match_ids:
            print(
                "  ⚠  No matches in DB. Run admin sync-matches first for realistic data."
            )
            print(
                "     Continuing without match subscriptions and challenge match refs...\n"
            )

        # 3. Subscriptions
        await seed_subscriptions(db, user_ids, match_ids)
        await db.commit()

        # 4. Google tokens
        await seed_google_tokens(db, user_ids)
        await db.commit()

        # 5. Alert logs
        await seed_alert_logs(db, user_ids, match_ids)
        await db.commit()

        # 6. Servers + members + challenges
        await seed_servers(db, user_ids, match_ids, args.servers)
        await db.commit()

        elapsed = (datetime.now() - t_start).total_seconds()
        print(f"\n  ✅ Seed complete in {elapsed:.1f}s")
        await print_summary(db)

        print(f"\n  Cleanup later with:")
        print(f"     python seed_db.py --db-url <url> --clean\n")

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the Football Alerts database")
    parser.add_argument(
        "--db-url",
        required=True,
        help="Database URL e.g. postgresql://user:pass@localhost:5432/football_alerts",
    )
    parser.add_argument(
        "--users",
        type=int,
        default=1000,
        help="Number of seed users to create (default: 1000)",
    )
    parser.add_argument(
        "--servers",
        type=int,
        default=50,
        help="Number of servers to create (default: 50)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without writing anything",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove all seed_ data before seeding",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Add more seed data even if seed users already exist",
    )
    args = parser.parse_args()
    asyncio.run(main(args))

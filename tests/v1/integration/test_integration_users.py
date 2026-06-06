"""
Integration tests for user profile and subscription endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestUserProfile:
    async def test_get_profile(self, auth_client: AsyncClient):
        res = await auth_client.get("/api/v1/users/me")
        assert res.status_code == 200
        data = res.json()
        assert "email" in data
        assert "full_name" in data

    async def test_update_name(self, auth_client: AsyncClient):
        res = await auth_client.patch(
            "/api/v1/users/me", json={"full_name": "Updated Name"}
        )
        assert res.status_code == 200
        assert res.json()["full_name"] == "Updated Name"

    async def test_get_profile_unauthenticated(self, client: AsyncClient):
        res = await client.get("/api/v1/users/me")
        assert res.status_code == 401


@pytest.mark.asyncio
class TestSubscriptions:
    async def test_list_subscriptions_empty(self, auth_client: AsyncClient):
        res = await auth_client.get("/api/v1/users/me/subscriptions")
        assert res.status_code == 200
        assert isinstance(res.json()["items"], list)

    async def test_create_league_subscription(self, auth_client: AsyncClient):
        res = await auth_client.post(
            "/api/v1/users/me/subscriptions",
            json={
                "subscription_type": "league",
                "external_id": "PL",
                "display_name": "Premier League",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["subscription_type"] == "league"
        assert data["external_id"] == "PL"

    async def test_create_duplicate_subscription(self, auth_client: AsyncClient):
        payload = {
            "subscription_type": "league",
            "external_id": "SA",
            "display_name": "Serie A",
        }
        await auth_client.post("/api/v1/users/me/subscriptions", json=payload)
        res = await auth_client.post("/api/v1/users/me/subscriptions", json=payload)
        assert res.status_code in (400, 409)

    async def test_delete_subscription(self, auth_client: AsyncClient):
        create_res = await auth_client.post(
            "/api/v1/users/me/subscriptions",
            json={
                "subscription_type": "league",
                "external_id": "BL1",
                "display_name": "Bundesliga",
            },
        )
        sub_id = create_res.json()["id"]
        del_res = await auth_client.delete(f"/api/v1/users/me/subscriptions/{sub_id}")
        assert del_res.status_code == 204

    async def test_delete_unauthenticated(self, client: AsyncClient):
        res = await client.delete("/api/v1/users/me/subscriptions/999")
        assert res.status_code == 401

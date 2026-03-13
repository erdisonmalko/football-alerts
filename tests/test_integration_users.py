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
        res = await auth_client.patch("/api/v1/users/me", json={"full_name": "Updated Name"})
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
        assert isinstance(res.json(), list)

    async def test_create_league_subscription(self, auth_client: AsyncClient):
        res = await auth_client.post("/api/v1/users/me/subscriptions", json={
            "subscription_type": "league",
            "external_id": "PL",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["subscription_type"] == "league"
        assert data["external_id"] == "PL"

    async def test_create_duplicate_subscription(self, auth_client: AsyncClient):
        payload = {"subscription_type": "league", "external_id": "SA"}
        await auth_client.post("/api/v1/users/me/subscriptions", json=payload)
        res = await auth_client.post("/api/v1/users/me/subscriptions", json=payload)
        assert res.status_code == 400

    async def test_delete_subscription(self, auth_client: AsyncClient):
        create_res = await auth_client.post("/api/v1/users/me/subscriptions", json={
            "subscription_type": "league",
            "external_id": "BL1",
        })
        sub_id = create_res.json()["id"]
        del_res = await auth_client.delete(f"/api/v1/users/me/subscriptions/{sub_id}")
        assert del_res.status_code == 204

    async def test_delete_other_users_subscription(self, client: AsyncClient):
        # Register a second user
        await client.post("/api/v1/auth/register", json={
            "email": "other@example.com",
            "password": "OtherPass123!",
            "full_name": "Other User",
        })
        await client.post("/api/v1/auth/login", json={
            "email": "other@example.com",
            "password": "OtherPass123!",
        })
        create_res = await client.post("/api/v1/users/me/subscriptions", json={
            "subscription_type": "league",
            "external_id": "FL1",
        })
        sub_id = create_res.json()["id"]

        # Now a fresh (unauthenticated) client tries to delete it
        fresh = client  # already logged in as other — log out first
        await fresh.post("/api/v1/auth/logout")
        res = await fresh.delete(f"/api/v1/users/me/subscriptions/{sub_id}")
        assert res.status_code == 401
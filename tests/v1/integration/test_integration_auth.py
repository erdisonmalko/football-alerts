"""
Integration tests for auth endpoints.
"""

from app.v1.main import app
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "register.success@example.com",
                "password": "SecurePass123",
                "full_name": "New User",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "register.success@example.com"
        assert "password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {
            "email": "register.dup@example.com",
            "password": "Pass1234",
            "full_name": "Dup",
        }
        await client.post("/api/v1/auth/register", json=payload)
        res = await client.post("/api/v1/auth/register", json=payload)
        assert res.status_code in (400, 409)

    async def test_register_invalid_email(self, client: AsyncClient):
        res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "Pass1234",
                "full_name": "Bad Email",
            },
        )
        assert res.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "shortpass@example.com",
                "password": "123",
                "full_name": "Short",
            },
        )
        assert res.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success_sets_cookie(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login.success@example.com",
                "password": "LoginPass123",
                "full_name": "Login Test",
            },
        )
        res = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "login.success@example.com",
                "password": "LoginPass123",
            },
        )
        assert res.status_code == 200
        assert "access_token" in res.cookies

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login.wrongpass@example.com",
                "password": "CorrectPass123",
                "full_name": "Wrong Pass",
            },
        )
        res = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "login.wrongpass@example.com",
                "password": "WrongPass999",
            },
        )
        assert res.status_code == 401

    async def test_login_unknown_email(self, client: AsyncClient):
        res = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nobody@example.com",
                "password": "Whatever123",
            },
        )
        assert res.status_code == 401


@pytest.mark.asyncio
class TestMe:
    async def test_me_authenticated(self, auth_client: AsyncClient):
        res = await auth_client.get("/api/v1/auth/me")
        assert res.status_code == 200
        assert res.json()["email"] == "testuser@example.com"

    async def test_me_unauthenticated(self, client: AsyncClient):
        # Use a fresh client with no cookies
        from httpx import AsyncClient as FreshClient, ASGITransport

        async with FreshClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as fresh:
            res = await fresh.get("/api/v1/auth/me")
        assert res.status_code == 401

    async def test_logout_clears_session(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "logout.test@example.com",
                "password": "LogoutPass123",
                "full_name": "Logout Test",
            },
        )
        await client.post(
            "/api/v1/auth/login",
            data={
                "username": "logout.test@example.com",
                "password": "LogoutPass123",
            },
        )
        await client.post("/api/v1/auth/logout")
        res = await client.get("/api/v1/auth/me")
        assert res.status_code == 401

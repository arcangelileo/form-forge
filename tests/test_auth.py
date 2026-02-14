import pytest


async def _register(client, name="Test User", email="test@example.com", password="securepass123"):
    response = await client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    if response.status_code == 201 and "set-cookie" in response.headers:
        for h in response.headers.get_list("set-cookie"):
            if h.startswith("access_token="):
                client.cookies.set("access_token", h.split(";")[0].split("=", 1)[1])
    return response


@pytest.mark.asyncio
async def test_register_success(client):
    response = await _register(client)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test User"
    assert data["email"] == "test@example.com"
    assert data["plan"] == "free"
    assert "set-cookie" in response.headers


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await _register(client)
    response = await _register(client, email="test@example.com")
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_short_password(client):
    response = await client.post(
        "/api/auth/register",
        json={"name": "User", "email": "test@example.com", "password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    response = await client.post(
        "/api/auth/register",
        json={"name": "User", "email": "not-an-email", "password": "securepass123"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client):
    await _register(client)
    client.cookies.clear()
    response = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "securepass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "set-cookie" in response.headers


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await _register(client)
    client.cookies.clear()
    response = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "securepass123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client):
    await _register(client)
    response = await client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout(client):
    await _register(client)
    response = await client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"

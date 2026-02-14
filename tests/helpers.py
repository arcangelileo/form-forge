from httpx import AsyncClient


async def register_user(client: AsyncClient, name="Test User", email="test@example.com", password="securepass123"):
    """Register a user and set cookies on the client."""
    response = await client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert response.status_code == 201
    if "set-cookie" in response.headers:
        for cookie_header in response.headers.get_list("set-cookie"):
            if cookie_header.startswith("access_token="):
                token = cookie_header.split(";")[0].split("=", 1)[1]
                client.cookies.set("access_token", token)
    return response.json()


async def login_user(client: AsyncClient, email="test@example.com", password="securepass123"):
    """Login a user and set cookies on the client."""
    response = await client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    if "set-cookie" in response.headers:
        for cookie_header in response.headers.get_list("set-cookie"):
            if cookie_header.startswith("access_token="):
                token = cookie_header.split(";")[0].split("=", 1)[1]
                client.cookies.set("access_token", token)
    return response.json()

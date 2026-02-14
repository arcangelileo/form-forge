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
async def test_create_form(client):
    await _register(client)
    response = await client.post("/api/forms/", json={"name": "Contact Form"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Contact Form"
    assert data["uuid"]
    assert data["is_active"] is True
    assert data["allowed_origins"] == "*"
    assert data["submission_count"] == 0


@pytest.mark.asyncio
async def test_create_form_unauthenticated(client):
    response = await client.post("/api/forms/", json={"name": "Contact Form"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_form_with_options(client):
    await _register(client)
    response = await client.post(
        "/api/forms/",
        json={
            "name": "Newsletter",
            "allowed_origins": "https://example.com",
            "redirect_url": "https://example.com/thanks",
            "email_notifications": False,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["allowed_origins"] == "https://example.com"
    assert data["redirect_url"] == "https://example.com/thanks"
    assert data["email_notifications"] is False


@pytest.mark.asyncio
async def test_list_forms(client):
    await _register(client)
    await client.post("/api/forms/", json={"name": "Form 1"})

    response = await client.get("/api/forms/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["forms"]) == 1


@pytest.mark.asyncio
async def test_list_forms_only_own(client):
    await _register(client, email="user1@example.com")
    await client.post("/api/forms/", json={"name": "User1 Form"})
    client.cookies.clear()

    await _register(client, email="user2@example.com")
    await client.post("/api/forms/", json={"name": "User2 Form"})

    response = await client.get("/api/forms/")
    data = response.json()
    assert data["total"] == 1
    assert data["forms"][0]["name"] == "User2 Form"


@pytest.mark.asyncio
async def test_get_form(client):
    await _register(client)
    create_resp = await client.post("/api/forms/", json={"name": "My Form"})
    form_id = create_resp.json()["id"]

    response = await client.get(f"/api/forms/{form_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "My Form"


@pytest.mark.asyncio
async def test_get_form_not_found(client):
    await _register(client)
    response = await client.get("/api/forms/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_form(client):
    await _register(client)
    create_resp = await client.post("/api/forms/", json={"name": "Old Name"})
    form_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/forms/{form_id}",
        json={"name": "New Name", "is_active": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_delete_form(client):
    await _register(client)
    create_resp = await client.post("/api/forms/", json={"name": "To Delete"})
    form_id = create_resp.json()["id"]

    response = await client.delete(f"/api/forms/{form_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/forms/{form_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_modify_other_users_form(client):
    await _register(client, email="user1@example.com")
    create_resp = await client.post("/api/forms/", json={"name": "User1 Form"})
    form_id = create_resp.json()["id"]
    client.cookies.clear()

    await _register(client, email="user2@example.com")

    response = await client.put(
        f"/api/forms/{form_id}", json={"name": "Hacked"}
    )
    assert response.status_code == 404

    response = await client.delete(f"/api/forms/{form_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_free_plan_form_limit(client):
    await _register(client)
    resp1 = await client.post("/api/forms/", json={"name": "Form 1"})
    assert resp1.status_code == 201

    resp2 = await client.post("/api/forms/", json={"name": "Form 2"})
    assert resp2.status_code == 403
    assert "limit" in resp2.json()["detail"].lower()

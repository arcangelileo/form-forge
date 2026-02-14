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


async def _create_form(client, name="Contact Form", **kwargs):
    resp = await client.post("/api/forms/", json={"name": name, **kwargs})
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_submit_json(client):
    await _register(client)
    form = await _create_form(client)
    response = await client.post(
        f"/f/{form['uuid']}",
        json={"name": "John", "email": "john@example.com", "message": "Hello!"},
        headers={"accept": "application/json"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_submit_form_urlencoded(client):
    await _register(client)
    form = await _create_form(client)
    response = await client.post(
        f"/f/{form['uuid']}",
        data={"name": "John", "email": "john@example.com"},
        headers={"accept": "application/json"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_submit_html_response(client):
    await _register(client)
    form = await _create_form(client)
    response = await client.post(
        f"/f/{form['uuid']}",
        json={"name": "John"},
        headers={"accept": "text/html"},
    )
    assert response.status_code == 200
    assert "Thank you" in response.text


@pytest.mark.asyncio
async def test_submit_with_redirect(client):
    await _register(client)
    form = await _create_form(client, redirect_url="https://example.com/thanks")

    response = await client.post(
        f"/f/{form['uuid']}",
        json={"name": "John"},
        headers={"accept": "text/html"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "https://example.com/thanks"


@pytest.mark.asyncio
async def test_submit_nonexistent_form(client):
    response = await client.post(
        "/f/nonexistent-uuid",
        json={"name": "John"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_inactive_form(client):
    await _register(client)
    form = await _create_form(client)
    await client.put(f"/api/forms/{form['id']}", json={"is_active": False})
    response = await client.post(
        f"/f/{form['uuid']}",
        json={"name": "John"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_honeypot_spam_detection(client):
    await _register(client)
    form = await _create_form(client)
    response = await client.post(
        f"/f/{form['uuid']}",
        json={"name": "Bot", "_gotcha": "i am a bot", "email": "bot@spam.com"},
        headers={"accept": "application/json"},
    )
    assert response.status_code == 200

    subs_resp = await client.get(f"/api/forms/{form['id']}/submissions")
    assert subs_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_honeypot_empty_not_spam(client):
    await _register(client)
    form = await _create_form(client)
    response = await client.post(
        f"/f/{form['uuid']}",
        json={"name": "Real User", "_gotcha": "", "email": "real@example.com"},
        headers={"accept": "application/json"},
    )
    assert response.status_code == 200

    subs_resp = await client.get(f"/api/forms/{form['id']}/submissions")
    assert subs_resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_empty_submission_rejected(client):
    await _register(client)
    form = await _create_form(client)
    response = await client.post(
        f"/f/{form['uuid']}",
        json={},
        headers={"accept": "application/json"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_submissions_pagination(client):
    await _register(client)
    form = await _create_form(client)

    for i in range(25):
        await client.post(
            f"/f/{form['uuid']}",
            json={"name": f"User {i}", "email": f"user{i}@example.com"},
            headers={"accept": "application/json"},
        )

    resp1 = await client.get(f"/api/forms/{form['id']}/submissions?page=1&per_page=10")
    data1 = resp1.json()
    assert data1["total"] == 25
    assert len(data1["submissions"]) == 10

    resp3 = await client.get(f"/api/forms/{form['id']}/submissions?page=3&per_page=10")
    data3 = resp3.json()
    assert len(data3["submissions"]) == 5


@pytest.mark.asyncio
async def test_list_submissions_search(client):
    await _register(client)
    form = await _create_form(client)

    await client.post(
        f"/f/{form['uuid']}",
        json={"name": "Alice", "email": "alice@example.com"},
        headers={"accept": "application/json"},
    )
    await client.post(
        f"/f/{form['uuid']}",
        json={"name": "Bob", "email": "bob@example.com"},
        headers={"accept": "application/json"},
    )

    resp = await client.get(f"/api/forms/{form['id']}/submissions?search=Alice")
    data = resp.json()
    assert data["total"] == 1
    assert data["submissions"][0]["data"]["name"] == "Alice"


@pytest.mark.asyncio
async def test_cors_preflight(client):
    await _register(client)
    form = await _create_form(client)
    response = await client.options(
        f"/f/{form['uuid']}",
        headers={"origin": "https://example.com"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


@pytest.mark.asyncio
async def test_submission_cors_headers(client):
    await _register(client)
    form = await _create_form(client)
    response = await client.post(
        f"/f/{form['uuid']}",
        json={"name": "Test"},
        headers={"accept": "application/json", "origin": "https://example.com"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

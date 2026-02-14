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
async def test_landing_page(client):
    response = await client.get("/", headers={"accept": "text/html"})
    assert response.status_code == 200
    assert "FormForge" in response.text
    assert "Form endpoints" in response.text
    assert "pricing" in response.text.lower()


@pytest.mark.asyncio
async def test_landing_page_shows_dashboard_link_when_logged_in(client):
    await _register(client)
    response = await client.get("/", headers={"accept": "text/html"})
    assert response.status_code == 200
    assert "Dashboard" in response.text


@pytest.mark.asyncio
async def test_login_page(client):
    response = await client.get("/login", headers={"accept": "text/html"})
    assert response.status_code == 200
    assert "Log in" in response.text


@pytest.mark.asyncio
async def test_login_page_redirects_when_authenticated(client):
    await _register(client)
    response = await client.get("/login", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"


@pytest.mark.asyncio
async def test_register_page(client):
    response = await client.get("/register", headers={"accept": "text/html"})
    assert response.status_code == 200
    assert "Create your account" in response.text


@pytest.mark.asyncio
async def test_register_page_redirects_when_authenticated(client):
    await _register(client)
    response = await client.get("/register", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"


@pytest.mark.asyncio
async def test_dashboard_page_requires_auth(client):
    response = await client.get("/dashboard", headers={"accept": "text/html"}, follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["location"]


@pytest.mark.asyncio
async def test_dashboard_page_renders(client):
    await _register(client)
    response = await client.get("/dashboard", headers={"accept": "text/html"})
    assert response.status_code == 200
    assert "Your Forms" in response.text
    assert "No forms yet" in response.text


@pytest.mark.asyncio
async def test_dashboard_shows_forms(client):
    await _register(client)
    await client.post("/api/forms/", json={"name": "My Test Form"})
    response = await client.get("/dashboard", headers={"accept": "text/html"})
    assert response.status_code == 200
    assert "My Test Form" in response.text


@pytest.mark.asyncio
async def test_form_detail_page(client):
    await _register(client)
    form_resp = await client.post("/api/forms/", json={"name": "Detail Form"})
    form = form_resp.json()
    response = await client.get(f"/dashboard/forms/{form['id']}", headers={"accept": "text/html"})
    assert response.status_code == 200
    assert "Detail Form" in response.text
    assert "No submissions yet" in response.text
    assert "Embed Snippet" in response.text


@pytest.mark.asyncio
async def test_form_detail_page_not_found(client):
    await _register(client)
    response = await client.get("/dashboard/forms/9999", headers={"accept": "text/html"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_form_detail_shows_submissions(client):
    await _register(client)
    form_resp = await client.post("/api/forms/", json={"name": "Subs Form"})
    form = form_resp.json()
    await client.post(
        f"/f/{form['uuid']}",
        json={"name": "Alice", "email": "alice@test.com"},
        headers={"accept": "application/json"},
    )
    response = await client.get(f"/dashboard/forms/{form['id']}", headers={"accept": "text/html"})
    assert response.status_code == 200
    assert "Alice" in response.text
    assert "alice@test.com" in response.text

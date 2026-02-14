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


async def _create_form_with_submissions(client):
    await _register(client)
    form_resp = await client.post("/api/forms/", json={"name": "Contact Form"})
    form = form_resp.json()

    for i in range(3):
        await client.post(
            f"/f/{form['uuid']}",
            json={"name": f"User {i}", "email": f"user{i}@example.com", "message": f"Message {i}"},
            headers={"accept": "application/json"},
        )
    return form


@pytest.mark.asyncio
async def test_csv_export(client):
    form = await _create_form_with_submissions(client)

    response = await client.get(f"/api/forms/{form['id']}/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]

    content = response.text
    lines = content.strip().split("\n")
    assert len(lines) == 4  # header + 3 rows
    assert "email" in lines[0]
    assert "name" in lines[0]
    assert "message" in lines[0]


@pytest.mark.asyncio
async def test_csv_export_empty(client):
    await _register(client)
    form_resp = await client.post("/api/forms/", json={"name": "Empty Form"})
    form = form_resp.json()

    response = await client.get(f"/api/forms/{form['id']}/export/csv")
    assert response.status_code == 404
    assert "No submissions" in response.json()["detail"]


@pytest.mark.asyncio
async def test_csv_export_unauthorized(client):
    response = await client.get("/api/forms/1/export/csv")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_csv_export_other_users_form(client):
    form = await _create_form_with_submissions(client)
    client.cookies.clear()

    await _register(client, email="user2@example.com")

    response = await client.get(f"/api/forms/{form['id']}/export/csv")
    assert response.status_code == 404

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.routers.submissions import clear_rate_limits

# Allow more submissions in tests
settings.submissions_per_minute = 1000

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_formforge.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_database():
    clear_rate_limits()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _extract_token(response):
    """Extract access_token from Set-Cookie header."""
    if "set-cookie" in response.headers:
        for cookie_header in response.headers.get_list("set-cookie"):
            if cookie_header.startswith("access_token="):
                return cookie_header.split(";")[0].split("=", 1)[1]
    return None


async def _register_user(client: AsyncClient, name="Test User", email="test@example.com", password="securepass123"):
    """Register a user and set cookies on the client."""
    response = await client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert response.status_code == 201
    token = _extract_token(response)
    if token:
        client.cookies.set("access_token", token)
    return response.json()


@pytest.fixture
def register(client):
    """Fixture returning an async function to register users."""
    async def _register(name="Test User", email="test@example.com", password="securepass123"):
        return await _register_user(client, name, email, password)
    return _register

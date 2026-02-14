from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base
from app.routers import auth, forms, submissions, export, pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (Alembic will manage migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Form backend-as-a-service — instant API endpoints for HTML forms",
    lifespan=lifespan,
)

# Static files
app.mount("/static", StaticFiles(directory="src/app/static"), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(forms.router)
app.include_router(submissions.router)
app.include_router(export.router)
app.include_router(pages.router)


@app.exception_handler(401)
async def unauthorized_redirect(request: Request, exc):
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)
    detail = getattr(exc, "detail", "Not authenticated")
    return JSONResponse(status_code=401, content={"detail": detail})


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }

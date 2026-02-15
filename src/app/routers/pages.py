import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, get_optional_user
from app.config import settings
from app.database import get_db
from app.models import Form, Submission, User

router = APIRouter(tags=["pages"])
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request, user: User | None = Depends(get_optional_user)):
    return templates.TemplateResponse(
        request, "landing.html", {"user": user, "settings": settings}
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "login.html")


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "register.html")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Form).where(Form.owner_id == user.id).order_by(Form.created_at.desc())
    )
    forms = result.scalars().all()

    form_data = []
    total_submissions = 0
    for form in forms:
        count_result = await db.execute(
            select(func.count(Submission.id)).where(
                Submission.form_id == form.id, Submission.is_spam == False
            )
        )
        count = count_result.scalar()
        total_submissions += count
        form_data.append({"form": form, "submission_count": count})

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "forms": form_data,
            "total_forms": len(forms),
            "total_submissions": total_submissions,
            "settings": settings,
        },
    )


@router.get("/dashboard/forms/{form_id}", response_class=HTMLResponse)
async def form_detail_page(
    form_id: int,
    request: Request,
    page: int = 1,
    search: str = "",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Form).where(Form.id == form_id, Form.owner_id == user.id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    per_page = 20
    query = select(Submission).where(
        Submission.form_id == form.id, Submission.is_spam == False
    )
    if search:
        query = query.where(Submission.data.contains(search))

    count_query = select(func.count(Submission.id)).where(
        Submission.form_id == form.id, Submission.is_spam == False
    )
    if search:
        count_query = count_query.where(Submission.data.contains(search))
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    query = query.order_by(Submission.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    submissions_raw = result.scalars().all()

    submissions = []
    all_fields = set()
    for s in submissions_raw:
        data = json.loads(s.data)
        all_fields.update(data.keys())
        submissions.append({"id": s.id, "data": data, "created_at": s.created_at, "ip_address": s.ip_address})

    total_pages = max(1, (total + per_page - 1) // per_page)

    return templates.TemplateResponse(
        request,
        "form_detail.html",
        {
            "user": user,
            "form": form,
            "submissions": submissions,
            "all_fields": sorted(all_fields),
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "search": search,
            "settings": settings,
        },
    )

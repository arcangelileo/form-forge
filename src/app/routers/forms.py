import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Form, Submission, User
from app.schemas import FormCreate, FormListResponse, FormResponse, FormUpdate

router = APIRouter(prefix="/api/forms", tags=["forms"])

PLAN_LIMITS = {
    "free": 1,
    "starter": 10,
    "pro": 999999,
}


def form_to_response(form: Form, submission_count: int = 0) -> FormResponse:
    return FormResponse(
        id=form.id,
        uuid=form.uuid,
        name=form.name,
        allowed_origins=form.allowed_origins,
        redirect_url=form.redirect_url,
        email_notifications=form.email_notifications,
        notification_email=form.notification_email,
        is_active=form.is_active,
        created_at=form.created_at,
        submission_count=submission_count,
    )


@router.post("/", response_model=FormResponse, status_code=status.HTTP_201_CREATED)
async def create_form(
    data: FormCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    form_count_result = await db.execute(
        select(func.count(Form.id)).where(Form.owner_id == user.id)
    )
    form_count = form_count_result.scalar()
    limit = PLAN_LIMITS.get(user.plan, 1)
    if form_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Form limit reached for your plan ({user.plan}). Upgrade to create more forms.",
        )

    form = Form(
        name=data.name,
        owner_id=user.id,
        allowed_origins=data.allowed_origins,
        redirect_url=data.redirect_url,
        email_notifications=data.email_notifications,
        notification_email=data.notification_email or user.email,
    )
    db.add(form)
    await db.commit()
    await db.refresh(form)
    return form_to_response(form, 0)


@router.get("/", response_model=FormListResponse)
async def list_forms(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Form).where(Form.owner_id == user.id).order_by(Form.created_at.desc())
    )
    forms = result.scalars().all()

    form_responses = []
    for form in forms:
        count_result = await db.execute(
            select(func.count(Submission.id)).where(
                Submission.form_id == form.id, Submission.is_spam == False
            )
        )
        count = count_result.scalar()
        form_responses.append(form_to_response(form, count))

    return FormListResponse(forms=form_responses, total=len(form_responses))


@router.get("/{form_id}", response_model=FormResponse)
async def get_form(
    form_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Form).where(Form.id == form_id, Form.owner_id == user.id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")

    count_result = await db.execute(
        select(func.count(Submission.id)).where(
            Submission.form_id == form.id, Submission.is_spam == False
        )
    )
    count = count_result.scalar()
    return form_to_response(form, count)


@router.put("/{form_id}", response_model=FormResponse)
async def update_form(
    form_id: int,
    data: FormUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Form).where(Form.id == form_id, Form.owner_id == user.id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(form, field, value)

    await db.commit()
    await db.refresh(form)

    count_result = await db.execute(
        select(func.count(Submission.id)).where(
            Submission.form_id == form.id, Submission.is_spam == False
        )
    )
    count = count_result.scalar()
    return form_to_response(form, count)


@router.delete("/{form_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_form(
    form_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Form).where(Form.id == form_id, Form.owner_id == user.id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")

    await db.delete(form)
    await db.commit()


@router.get("/{form_id}/submissions")
async def list_submissions(
    form_id: int,
    page: int = 1,
    per_page: int = 20,
    search: str = "",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Form).where(Form.id == form_id, Form.owner_id == user.id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")

    query = select(Submission).where(
        Submission.form_id == form.id, Submission.is_spam == False
    )
    if search:
        query = query.where(Submission.data.contains(search))

    count_result = await db.execute(
        select(func.count(Submission.id)).where(
            Submission.form_id == form.id, Submission.is_spam == False
        ).where(Submission.data.contains(search) if search else True)
    )
    total = count_result.scalar()

    query = query.order_by(Submission.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    submissions = result.scalars().all()

    return {
        "submissions": [
            {
                "id": s.id,
                "data": json.loads(s.data),
                "ip_address": s.ip_address,
                "is_spam": s.is_spam,
                "created_at": s.created_at.isoformat(),
            }
            for s in submissions
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }

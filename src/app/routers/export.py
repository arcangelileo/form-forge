import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Form, Submission, User

router = APIRouter(prefix="/api/forms", tags=["export"])


@router.get("/{form_id}/export/csv")
async def export_csv(
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

    result = await db.execute(
        select(Submission)
        .where(Submission.form_id == form.id, Submission.is_spam == False)
        .order_by(Submission.created_at.desc())
    )
    submissions = result.scalars().all()

    if not submissions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No submissions to export",
        )

    # Collect all unique field names across submissions
    all_fields = set()
    parsed = []
    for s in submissions:
        data = json.loads(s.data)
        all_fields.update(data.keys())
        parsed.append({"_id": s.id, "_submitted_at": s.created_at.isoformat(), **data})

    fieldnames = ["_id", "_submitted_at"] + sorted(all_fields)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in parsed:
        writer.writerow(row)

    output.seek(0)
    filename = f"{form.name.replace(' ', '_')}_submissions.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

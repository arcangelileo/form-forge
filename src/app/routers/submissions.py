import json
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Form, Submission

router = APIRouter(tags=["submissions"])

# In-memory rate limiting store: { form_uuid: { ip: [timestamps] } }
_rate_limit_store: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))


def clear_rate_limits():
    _rate_limit_store.clear()


def _check_rate_limit(form_uuid: str, ip: str) -> bool:
    now = time.time()
    window = 60.0
    timestamps = _rate_limit_store[form_uuid][ip]
    # Clean old entries
    _rate_limit_store[form_uuid][ip] = [t for t in timestamps if now - t < window]
    if len(_rate_limit_store[form_uuid][ip]) >= settings.submissions_per_minute:
        return False
    _rate_limit_store[form_uuid][ip].append(now)
    return True


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_cors(form: Form, request: Request) -> dict[str, str]:
    origin = request.headers.get("origin", "")
    allowed = form.allowed_origins.strip()
    headers = {}
    if allowed == "*":
        headers["Access-Control-Allow-Origin"] = "*"
    elif origin:
        allowed_list = [o.strip() for o in allowed.split(",")]
        if origin in allowed_list:
            headers["Access-Control-Allow-Origin"] = origin
    headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    headers["Access-Control-Allow-Headers"] = "Content-Type"
    return headers


@router.options("/f/{form_uuid}")
async def submission_preflight(
    form_uuid: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Form).where(Form.uuid == form_uuid))
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")

    cors_headers = _check_cors(form, request)
    return Response(status_code=200, headers=cors_headers)


@router.post("/f/{form_uuid}")
async def submit_form(
    form_uuid: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Form).where(Form.uuid == form_uuid))
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")

    if not form.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Form is inactive")

    client_ip = _get_client_ip(request)

    # Rate limiting
    if not _check_rate_limit(form_uuid, client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )

    # Parse form data (URL-encoded or JSON)
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            data = await request.json()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON"
            )
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form_data = await request.form()
        data = {k: v for k, v in form_data.items()}
    else:
        # Try JSON first, fall back to form data
        try:
            data = await request.json()
        except Exception:
            try:
                form_data = await request.form()
                data = {k: v for k, v in form_data.items()}
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to parse request body",
                )

    # Honeypot spam detection
    is_spam = False
    if "_gotcha" in data:
        if data["_gotcha"]:
            is_spam = True
        del data["_gotcha"]

    # Remove internal fields
    clean_data = {k: v for k, v in data.items() if not k.startswith("_")}

    if not clean_data and not is_spam:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No form data received"
        )

    submission = Submission(
        form_id=form.id,
        data=json.dumps(clean_data),
        ip_address=client_ip,
        is_spam=is_spam,
    )
    db.add(submission)
    await db.commit()

    cors_headers = _check_cors(form, request)

    # Determine response based on accept header and redirect URL
    accept = request.headers.get("accept", "")

    if form.redirect_url and "text/html" in accept:
        response = RedirectResponse(
            url=form.redirect_url, status_code=status.HTTP_303_SEE_OTHER
        )
        for k, v in cors_headers.items():
            response.headers[k] = v
        return response

    if "text/html" in accept and "application/json" not in accept:
        html = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Thank you!</title>
<style>body{font-family:system-ui,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;background:#f8fafc;}
.card{text-align:center;padding:3rem;background:white;border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,0.08);}
h1{color:#0f172a;margin:0 0 0.5rem;}p{color:#64748b;margin:0;}</style></head>
<body><div class="card"><h1>Thank you!</h1><p>Your submission has been received.</p></div></body>
</html>"""
        return HTMLResponse(content=html, headers=cors_headers)

    return Response(
        content=json.dumps({"status": "ok", "message": "Submission received"}),
        media_type="application/json",
        headers=cors_headers,
    )

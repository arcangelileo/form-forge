import asyncio
import json
import logging
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.email_service import send_submission_notification
from app.models import Form, Submission

logger = logging.getLogger(__name__)

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

    # Send email notification (fire-and-forget, don't block the response)
    if not is_spam and form.email_notifications and form.notification_email:
        asyncio.create_task(
            send_submission_notification(
                to_email=form.notification_email,
                form_name=form.name,
                submission_data=clean_data,
            )
        )

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
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thank you!</title>
<style>
*{box-sizing:border-box}
body{font-family:'Inter',system-ui,-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;background:linear-gradient(135deg,#eff6ff 0%,#f8fafc 50%,#eef2ff 100%);}
.card{text-align:center;padding:3rem 2.5rem;background:white;border-radius:16px;box-shadow:0 4px 32px rgba(0,0,0,0.06);max-width:420px;width:90%;}
.icon{width:64px;height:64px;background:#dcfce7;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 1.25rem;}
.icon svg{width:32px;height:32px;color:#16a34a;}
h1{color:#0f172a;margin:0 0 0.5rem;font-size:1.5rem;font-weight:700;}
p{color:#64748b;margin:0;font-size:0.95rem;line-height:1.5;}
.powered{margin-top:2rem;font-size:0.75rem;color:#94a3b8;}
.powered a{color:#3b82f6;text-decoration:none;}
</style></head>
<body>
<div class="card">
  <div class="icon"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg></div>
  <h1>Thank you!</h1>
  <p>Your submission has been received successfully. We'll be in touch soon.</p>
  <p class="powered">Powered by <a href="/">FormForge</a></p>
</div>
</body>
</html>"""
        return HTMLResponse(content=html, headers=cors_headers)

    return Response(
        content=json.dumps({"status": "ok", "message": "Submission received"}),
        media_type="application/json",
        headers=cors_headers,
    )

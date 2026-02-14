import html
import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def send_submission_notification(
    to_email: str,
    form_name: str,
    submission_data: dict,
):
    if not settings.smtp_host:
        logger.info(f"SMTP not configured, skipping notification to {to_email}")
        return

    try:
        import aiosmtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        # Build a clean HTML email (escape all user-provided content)
        fields_html = ""
        for key, value in submission_data.items():
            safe_key = html.escape(str(key))
            safe_value = html.escape(str(value))
            fields_html += f"""
            <tr>
                <td style="padding:8px 12px;border-bottom:1px solid #e2e8f0;font-weight:600;color:#374151;width:30%;vertical-align:top;">{safe_key}</td>
                <td style="padding:8px 12px;border-bottom:1px solid #e2e8f0;color:#1f2937;">{safe_value}</td>
            </tr>"""

        safe_form_name = html.escape(str(form_name))
        html_body = f"""
        <div style="font-family:system-ui,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#2563eb;color:white;padding:20px 24px;border-radius:8px 8px 0 0;">
                <h2 style="margin:0;font-size:18px;">New Submission: {safe_form_name}</h2>
            </div>
            <div style="background:white;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;padding:0;">
                <table style="width:100%;border-collapse:collapse;">{fields_html}</table>
            </div>
            <p style="text-align:center;color:#94a3b8;font-size:12px;margin-top:16px;">
                Sent by FormForge
            </p>
        </div>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"New submission: {form_name}"
        msg["From"] = settings.smtp_from_email
        msg["To"] = to_email

        # Plain text version
        text_body = f"New submission for {form_name}:\n\n"
        for key, value in submission_data.items():
            text_body += f"{key}: {value}\n"

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user or None,
            password=settings.smtp_password or None,
            use_tls=settings.smtp_use_tls,
        )
        logger.info(f"Notification sent to {to_email} for form {form_name}")

    except Exception as e:
        logger.error(f"Failed to send notification to {to_email}: {e}")

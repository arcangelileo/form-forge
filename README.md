# FormForge

**Form backend-as-a-service** — Instant API endpoints for HTML forms.

Point any `<form>` tag at a FormForge endpoint and submissions are captured, stored, and forwarded via email — no server code needed. Think Formspree or Basin, but self-hostable and simple.

---

## Features

- **Instant form endpoints** — Create endpoints in seconds, each with a unique URL (`/f/{uuid}`)
- **Flexible input** — Accepts JSON, URL-encoded, and multipart form data
- **Dashboard** — View, search, and paginate through submissions with a clean UI
- **Email notifications** — Get notified on new submissions via SMTP (SendGrid, Mailgun, etc.)
- **Spam protection** — Built-in honeypot field (`_gotcha`) and IP-based rate limiting
- **CSV export** — Download all submissions as CSV with one click
- **Embeddable snippets** — Copy-paste HTML snippets with built-in spam protection
- **Custom redirects** — Send users to your own thank-you page after submission
- **Per-form CORS** — Configure allowed origins per form, or allow all with `*`
- **Plan-based limits** — Free, Starter, and Pro tiers with configurable form/submission quotas
- **Self-hostable** — Single Docker image, SQLite database, zero external dependencies

---

## Quick Start

### Docker (one command)

```bash
docker run -d \
  -p 8000:8000 \
  -e FORMFORGE_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))") \
  -v formforge-data:/app/data \
  --name formforge \
  ghcr.io/arcangelileo/form-forge:latest
```

Then open [http://localhost:8000](http://localhost:8000).

### Docker Compose

```bash
git clone https://github.com/arcangelileo/form-forge.git
cd form-forge
cp .env.example .env
# Edit .env — at minimum change FORMFORGE_SECRET_KEY
docker compose up -d
```

### Local Development

```bash
# Clone and install
git clone https://github.com/arcangelileo/form-forge.git
cd form-forge
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Configure
cp .env.example .env

# Run the app
PYTHONPATH=src uvicorn app.main:app --reload --app-dir src

# Run the test suite
PYTHONPATH=src pytest tests/ -v
```

---

## Usage

### 1. Create an account

Go to `/register` and sign up. You'll be redirected to the dashboard.

### 2. Create a form endpoint

Click **"New Form"** in the dashboard. Give it a name (e.g., "Contact Form") and configure options like allowed origins, redirect URL, and email notifications.

### 3. Point your HTML form at the endpoint

```html
<form action="https://your-server.com/f/your-form-uuid" method="POST">
  <!-- Honeypot field — keep this hidden to filter bots -->
  <input type="text" name="_gotcha" style="display:none" tabindex="-1" autocomplete="off">

  <label for="name">Name</label>
  <input type="text" name="name" id="name" required>

  <label for="email">Email</label>
  <input type="email" name="email" id="email" required>

  <label for="message">Message</label>
  <textarea name="message" id="message"></textarea>

  <button type="submit">Send</button>
</form>
```

### 4. Submit via JavaScript (optional)

```javascript
fetch("https://your-server.com/f/your-form-uuid", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    name: "Jane Doe",
    email: "jane@example.com",
    message: "Hello from JS!"
  })
});
```

### 5. View & export submissions

Open the form detail page in the dashboard to search, paginate, and export submissions as CSV.

---

## API Reference

### Authentication

All API endpoints (except form submission and public pages) require authentication via an `access_token` httponly cookie set during login/register.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/register` | Create a new account |
| `POST` | `/api/auth/login` | Log in and receive auth cookie |
| `POST` | `/api/auth/logout` | Clear auth cookie |
| `GET` | `/api/auth/me` | Get current authenticated user |

**Register / Login request body:**

```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "securepassword"
}
```

### Forms

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/forms/` | List all forms for the authenticated user |
| `POST` | `/api/forms/` | Create a new form |
| `GET` | `/api/forms/{id}` | Get a single form |
| `PUT` | `/api/forms/{id}` | Update a form |
| `DELETE` | `/api/forms/{id}` | Delete a form and all its submissions |

**Create form request body:**

```json
{
  "name": "Contact Form",
  "allowed_origins": "*",
  "redirect_url": "https://example.com/thanks",
  "email_notifications": true,
  "notification_email": "alerts@example.com"
}
```

### Submissions

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/f/{form_uuid}` | Submit data to a form (public, CORS-enabled) |
| `OPTIONS` | `/f/{form_uuid}` | CORS preflight |
| `GET` | `/api/forms/{id}/submissions` | List submissions (paginated) |

**Query parameters for listing submissions:**

| Param | Default | Description |
|-------|---------|-------------|
| `page` | `1` | Page number |
| `per_page` | `20` | Results per page |
| `search` | `""` | Full-text search in submission data |

### Export

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/forms/{id}/export/csv` | Download all submissions as CSV |

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check (returns app name and version) |

---

## Configuration

All settings are configured via environment variables with the `FORMFORGE_` prefix. They can also be set in a `.env` file.

| Variable | Default | Description |
|----------|---------|-------------|
| `FORMFORGE_SECRET_KEY` | `change-me-in-production` | **Required.** Secret key for signing JWT tokens. |
| `FORMFORGE_BASE_URL` | `http://localhost:8000` | Public URL shown in snippet generator and emails. |
| `FORMFORGE_DATABASE_URL` | `sqlite+aiosqlite:///./formforge.db` | Async SQLAlchemy database URL. |
| `FORMFORGE_DEBUG` | `false` | Enable debug mode (verbose logging). |
| `FORMFORGE_SMTP_HOST` | *(empty)* | SMTP hostname. Leave empty to disable email. |
| `FORMFORGE_SMTP_PORT` | `587` | SMTP port. |
| `FORMFORGE_SMTP_USER` | *(empty)* | SMTP username. |
| `FORMFORGE_SMTP_PASSWORD` | *(empty)* | SMTP password. |
| `FORMFORGE_SMTP_FROM_EMAIL` | `noreply@formforge.dev` | Sender address for notification emails. |
| `FORMFORGE_SMTP_USE_TLS` | `true` | Use STARTTLS for SMTP connections. |
| `FORMFORGE_SUBMISSIONS_PER_MINUTE` | `10` | Rate limit: max submissions per IP per form per minute. |

### SMTP Provider Examples

**SendGrid:**
```env
FORMFORGE_SMTP_HOST=smtp.sendgrid.net
FORMFORGE_SMTP_PORT=587
FORMFORGE_SMTP_USER=apikey
FORMFORGE_SMTP_PASSWORD=SG.your-api-key-here
FORMFORGE_SMTP_FROM_EMAIL=forms@yourdomain.com
```

**Mailgun:**
```env
FORMFORGE_SMTP_HOST=smtp.mailgun.org
FORMFORGE_SMTP_PORT=587
FORMFORGE_SMTP_USER=postmaster@mg.yourdomain.com
FORMFORGE_SMTP_PASSWORD=your-mailgun-password
FORMFORGE_SMTP_FROM_EMAIL=forms@yourdomain.com
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Public Internet                       │
│                                                         │
│  Static Site / SPA ──POST /f/{uuid}──▶ FormForge API    │
│                                        │                │
│  Browser ──GET /dashboard──▶ Dashboard UI               │
└─────────────────────────────────────────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │              FastAPI App                 │
                    │                                         │
                    │  Routers:                               │
                    │  ├── /api/auth/*     (JWT auth)         │
                    │  ├── /api/forms/*    (CRUD + list)      │
                    │  ├── /f/{uuid}       (submissions)      │
                    │  ├── /api/forms/*/export/csv             │
                    │  └── /*              (Jinja2 pages)     │
                    │                                         │
                    │  Services:                              │
                    │  ├── auth.py         (JWT + bcrypt)     │
                    │  ├── email_service   (aiosmtplib)      │
                    │  └── rate limiter    (in-memory)        │
                    │                                         │
                    │  Database:                              │
                    │  └── SQLite via async SQLAlchemy        │
                    │      ├── users                          │
                    │      ├── forms                          │
                    │      └── submissions (JSON blob data)   │
                    └─────────────────────────────────────────┘
```

### Key Design Decisions

- **JSON blob storage** — Submission data is stored as a JSON string, so forms can have any fields without schema migrations.
- **Async everywhere** — FastAPI + async SQLAlchemy + aiosmtplib for high concurrency on a single process.
- **Honeypot spam filter** — A hidden `_gotcha` field that bots fill in; if present, the submission is silently marked as spam.
- **JWT in httponly cookies** — Secure, XSS-resistant authentication without client-side token storage.
- **Fire-and-forget emails** — Notifications are sent via `asyncio.create_task()` so they don't block the submission response.

### Project Structure

```
form-forge/
├── Dockerfile              # Multi-stage production build
├── docker-compose.yml      # One-command deployment
├── pyproject.toml          # Dependencies and build config
├── alembic.ini             # Database migration config
├── .env.example            # Environment variable reference
├── alembic/
│   ├── env.py              # Async Alembic setup
│   └── versions/           # Migration scripts
├── src/app/
│   ├── main.py             # FastAPI app, lifespan, error handlers
│   ├── config.py           # pydantic-settings configuration
│   ├── database.py         # Async SQLAlchemy engine & session
│   ├── models.py           # User, Form, Submission ORM models
│   ├── auth.py             # JWT creation, password hashing, auth deps
│   ├── schemas.py          # Pydantic request/response schemas
│   ├── email_service.py    # SMTP notification sender
│   ├── routers/
│   │   ├── auth.py         # Register, login, logout, /me
│   │   ├── forms.py        # Form CRUD + submission listing
│   │   ├── submissions.py  # POST /f/{uuid}, CORS, rate limiting
│   │   ├── export.py       # CSV export
│   │   └── pages.py        # Jinja2 HTML page routes
│   ├── static/             # Static assets
│   └── templates/          # Jinja2 HTML templates
│       ├── base.html       # Base layout with Tailwind CSS
│       ├── landing.html    # Public landing page with pricing
│       ├── login.html      # Login page
│       ├── register.html   # Registration page
│       ├── dashboard.html  # Dashboard with form management
│       └── form_detail.html # Submission viewer + snippet generator
└── tests/                  # 54 tests (pytest + httpx)
    ├── conftest.py         # Test DB setup, fixtures
    ├── test_health.py      # Health endpoint (2)
    ├── test_auth.py        # Auth flows (10)
    ├── test_forms.py       # Form CRUD (11)
    ├── test_submissions.py # Submissions + spam (13)
    ├── test_export.py      # CSV export (4)
    ├── test_pages.py       # Page rendering (12)
    └── test_rate_limit.py  # Rate limiting (2)
```

---

## Pricing Tiers

| Feature | Free | Starter ($9/mo) | Pro ($29/mo) |
|---------|------|-----------------|--------------|
| Forms | 1 | 10 | Unlimited |
| Submissions/month | 50 | 1,000 | 10,000 |
| Email notifications | — | Yes | Yes |
| CSV export | — | Yes | Yes |
| Custom redirects | — | — | Yes |
| File uploads | — | — | Coming soon |
| Webhooks | — | — | Coming soon |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Make your changes and write tests
5. Run the test suite: `PYTHONPATH=src pytest tests/ -v`
6. Lint with ruff: `ruff check src/ tests/`
7. Commit and push, then open a pull request

---

## License

MIT

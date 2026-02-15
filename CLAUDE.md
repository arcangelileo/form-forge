# FormForge

Phase: COMPLETE

## Project Spec
- **Repo**: https://github.com/arcangelileo/form-forge
- **Idea**: FormForge is a form backend-as-a-service that gives developers and marketers instant API endpoints for HTML forms. Point any `<form>` tag at a FormForge endpoint, and submissions are captured, stored, and forwarded via email — no server code needed. Users get a dashboard to view, search, and export submissions, manage multiple forms/projects, configure email notifications and spam filtering, and generate embeddable form snippets. Think Formspree or Basin, but self-hostable and simple.
- **Target users**: Frontend developers, indie hackers, agencies, and marketers who build static sites, landing pages, and JAMstack apps and need a reliable form backend without writing server code.
- **Revenue model**: Freemium with usage tiers. Free tier: 1 form, 50 submissions/month. Starter ($9/mo): 10 forms, 1,000 submissions/month, email notifications. Pro ($29/mo): unlimited forms, 10,000 submissions/month, custom thank-you redirects, file uploads, webhooks, CSV/JSON export.
- **Tech stack**: Python 3.11+, FastAPI, SQLite (via async SQLAlchemy + aiosqlite), Alembic, Jinja2 + Tailwind CSS (CDN), APScheduler, Docker
- **MVP scope**:
  1. User registration & login (JWT + httponly cookies)
  2. Create/manage form endpoints (each gets a unique URL)
  3. Accept form submissions via POST (CORS-enabled, handles URL-encoded and JSON)
  4. Dashboard: view submissions per form, search, pagination
  5. Email notifications on new submissions (configurable per form)
  6. Spam protection (honeypot field + rate limiting)
  7. Custom thank-you redirect URL per form
  8. CSV export of submissions
  9. Embeddable HTML snippet generator
  10. Public landing page with pricing

## Architecture Decisions
- **Form endpoint format**: `POST /f/{form_uuid}` — short, clean, easy to embed
- **Submission storage**: JSON blob column for flexible form fields (no fixed schema per form)
- **CORS**: Per-form allowed origins configuration, defaults to `*` for easy setup
- **Email**: SMTP via aiosmtplib, configurable per-instance (SendGrid, Mailgun, or raw SMTP)
- **Spam**: Honeypot field (`_gotcha` — if filled, silently discard) + IP-based rate limiting (10 submissions/min per form)
- **Auth**: JWT tokens in httponly cookies, bcrypt password hashing (consistent with factory pattern)
- **Background jobs**: APScheduler for email sending queue and periodic cleanup of expired/over-quota submissions
- **File uploads**: Deferred to post-MVP (Pro tier feature)
- **Webhooks**: Deferred to post-MVP (Pro tier feature)
- **Rate limiting**: In-memory for MVP, Redis for production scale

## Task Backlog
- [x] Create GitHub repo and initial project structure (pyproject.toml, src/app/, alembic)
- [x] Set up FastAPI app skeleton with health check and configuration
- [x] Create database models (User, Form, Submission) and Alembic migrations
- [x] Implement user registration and login (JWT auth with httponly cookies)
- [x] Build form CRUD API (create, list, update, delete form endpoints)
- [x] Implement form submission endpoint (`POST /f/{form_uuid}`) with CORS
- [x] Build dashboard UI — form list, submission viewer with search and pagination
- [x] Add email notification system (background job on new submission)
- [x] Implement spam protection (honeypot + rate limiting)
- [x] Add CSV export for form submissions
- [x] Build embeddable snippet generator UI
- [x] Create public landing page with feature list and pricing
- [x] Write comprehensive tests (auth, submissions, API, spam)
- [x] Write Dockerfile and docker-compose.yml
- [x] Write README with setup and deploy instructions

## Progress Log
### Session 1 — IDEATION
- Chose idea: FormForge (form backend-as-a-service)
- Created spec and backlog
- Key differentiator: simple, self-hostable, developer-friendly form endpoints

### Session 2 — SCAFFOLDING
- Created GitHub repo and project structure
- Set up pyproject.toml with all dependencies (FastAPI, SQLAlchemy, Alembic, etc.)
- Created FastAPI app skeleton with `/health` endpoint
- Created config module with pydantic-settings (env-var driven)
- Created database models: User, Form, Submission (async SQLAlchemy)
- Set up Alembic with async SQLAlchemy support
- Created test infrastructure (conftest.py with test DB isolation)
- Health check tests passing (2/2)
- Phase changed to DEVELOPMENT

### Session 3 — FULL MVP IMPLEMENTATION
- Implemented JWT auth with httponly cookies (register, login, logout, /me)
  - Fixed JWT `sub` claim to use string (jose library requires string subjects)
  - bcrypt password hashing via passlib
- Built form CRUD API (create, list, get, update, delete)
  - Plan-based form limits (free: 1, starter: 10, pro: unlimited)
  - Owner-scoped access (users can only see/modify their own forms)
- Implemented form submission endpoint (`POST /f/{form_uuid}`)
  - Accepts JSON, URL-encoded, and multipart form data
  - Per-form CORS configuration with preflight support
  - Honeypot spam detection (`_gotcha` field)
  - IP-based rate limiting (configurable per-minute limit)
  - Custom redirect URLs or default thank-you page
- Built full dashboard UI with Tailwind CSS
  - Stats overview (total forms, submissions, plan)
  - Form list with create/edit/delete modals
  - Submission viewer with search, pagination, and data table
  - Embeddable HTML snippet generator with copy-to-clipboard
  - Empty states, loading states, toast notifications
- Built public landing page with hero, features, how-it-works, and pricing
- Built login/register pages with split-panel design
- Added CSV export (dynamic column detection across all submissions)
- Added email notification service (SMTP via aiosmtplib, HTML + plain text)
- Wrote 40 comprehensive tests — all passing:
  - Auth: register, login, logout, validation, duplicate detection
  - Forms: CRUD, ownership isolation, plan limits
  - Submissions: JSON/form-encoded, CORS, honeypot, redirects, pagination, search
  - Export: CSV download, empty state, authorization
- Created Dockerfile and docker-compose.yml
- Created README with setup instructions, API docs, and configuration reference
- Phase changed to QA

### Session 4 — QA & POLISH
- **Initial test run**: All 40 existing tests passed
- **Full code audit** of every source file and template
- **Bugs found and fixed**:
  1. **XSS in email notifications** — User-submitted form data was injected directly into HTML emails without escaping. Fixed by using `html.escape()` on all user content in `email_service.py`
  2. **XSS in dashboard edit modal** — Form names with quotes/apostrophes broke inline `onclick` handlers. Replaced unsafe inline JS with `data-*` attributes and event delegation in `dashboard.html`
  3. **Hardcoded static files path** — `main.py` used `directory="src/app/static"` which would fail in Docker. Fixed to use `Path(__file__)` relative resolution
  4. **Hardcoded templates path** — `pages.py` used `directory="src/app/templates"` which would fail in Docker. Fixed to use `Path(__file__)` relative resolution
  5. **Email notifications never sent** — `submit_form()` in `submissions.py` never called `send_submission_notification`. Wired up fire-and-forget async task via `asyncio.create_task()`
  6. **Deprecated TemplateResponse API** — Fixed `TemplateResponse(name, {request: ...})` to `TemplateResponse(request, name, {})` to eliminate deprecation warnings
- **UI polish**:
  - Added SVG favicon to all pages via `base.html`
  - Enhanced thank-you page with gradient background, checkmark icon, powered-by branding
  - Added CTA section before footer on landing page
  - Added "How it works" and "Pricing" nav links to landing page header and footer
  - Added smooth scrolling for anchor links
- **Test coverage expanded** (40 → 54 tests):
  - `test_pages.py` (12 tests): Landing page rendering, login/register redirects, dashboard auth guard, dashboard rendering with/without forms, form detail page with submissions, 404 handling
  - `test_rate_limit.py` (2 tests): Rate limiting enforcement, per-form rate limit isolation
- **Final result**: 54 tests, all passing, zero warnings
- Phase changed to DEPLOYMENT

### Session 5 — DEPLOYMENT & FINALIZATION
- **Dockerfile**: Rebuilt as multi-stage build (builder + runtime) for smaller image size
  - Non-root `formforge` user for security
  - `HEALTHCHECK` via curl to `/health`
  - Exec-form `CMD` for proper PID 1 signal handling
  - Installed curl in runtime stage for health checks
- **docker-compose.yml**: Updated with all environment variables, configurable host port
- **.env.example**: Expanded with section headers, inline documentation, secret key generation command, and `FORMFORGE_PORT` for Docker Compose
- **README.md**: Comprehensive rewrite with:
  - Feature list, quick start (Docker one-liner, Compose, local dev)
  - Full usage walkthrough (HTML form + JavaScript examples)
  - Complete API reference (auth, forms, submissions, export, health)
  - Configuration table with all env vars
  - SMTP provider examples (SendGrid, Mailgun)
  - Architecture diagram and key design decisions
  - Project structure tree
  - Pricing tiers table
  - Contributing guidelines
- **Code cleanup**:
  - Removed unused imports (`Request` from `routers/auth.py`, `status` from `routers/pages.py`)
  - Added ruff `E712` ignore for SQLAlchemy boolean column comparisons
  - All 54 tests passing, ruff lint clean
- Phase changed to COMPLETE

## Known Issues
(none)

## Files Structure
```
form-forge/
├── CLAUDE.md
├── README.md
├── .gitignore
├── .env.example
├── pyproject.toml
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py              # FastAPI app, lifespan, routers, error handlers
│       ├── config.py            # Settings via pydantic-settings
│       ├── database.py          # Async SQLAlchemy engine & session
│       ├── models.py            # User, Form, Submission models
│       ├── auth.py              # JWT token creation, password hashing, auth deps
│       ├── schemas.py           # Pydantic request/response schemas
│       ├── email_service.py     # SMTP email notification sender
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── auth.py          # Register, login, logout, /me endpoints
│       │   ├── forms.py         # Form CRUD + submission listing API
│       │   ├── submissions.py   # POST /f/{uuid} submission endpoint + CORS
│       │   ├── export.py        # CSV export endpoint
│       │   └── pages.py         # Jinja2 HTML page routes (dashboard, landing)
│       ├── static/
│       │   └── .gitkeep
│       └── templates/
│           ├── base.html         # Base template with Tailwind, toast system
│           ├── landing.html      # Public landing page with pricing
│           ├── login.html        # Login page
│           ├── register.html     # Registration page
│           ├── dashboard.html    # Dashboard with form management
│           └── form_detail.html  # Submission viewer + snippet generator
└── tests/
    ├── __init__.py
    ├── conftest.py              # Test DB setup, fixtures, rate limit reset
    ├── helpers.py               # Test helper utilities
    ├── test_health.py           # Health endpoint tests (2)
    ├── test_auth.py             # Auth tests (10)
    ├── test_forms.py            # Form CRUD tests (11)
    ├── test_submissions.py      # Submission + spam tests (13)
    ├── test_export.py           # CSV export tests (4)
    ├── test_pages.py            # Page rendering tests (12)
    └── test_rate_limit.py       # Rate limiting tests (2)
```

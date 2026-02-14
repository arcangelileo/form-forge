# FormForge

Phase: QA

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
    └── test_export.py           # CSV export tests (4)
```

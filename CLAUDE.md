# FormForge

Phase: DEVELOPMENT

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
- [ ] Implement user registration and login (JWT auth with httponly cookies)
- [ ] Build form CRUD API (create, list, update, delete form endpoints)
- [ ] Implement form submission endpoint (`POST /f/{form_uuid}`) with CORS
- [ ] Build dashboard UI — form list, submission viewer with search and pagination
- [ ] Add email notification system (background job on new submission)
- [ ] Implement spam protection (honeypot + rate limiting)
- [ ] Add CSV export for form submissions
- [ ] Build embeddable snippet generator UI
- [ ] Create public landing page with feature list and pricing
- [ ] Write comprehensive tests (auth, submissions, API, spam)
- [ ] Write Dockerfile and docker-compose.yml
- [ ] Write README with setup and deploy instructions

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

## Known Issues
(none yet)

## Files Structure
```
form-forge/
├── CLAUDE.md
├── .gitignore
├── .env.example
├── pyproject.toml
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py          # FastAPI app, lifespan, health check
│       ├── config.py         # Settings via pydantic-settings
│       ├── database.py       # Async SQLAlchemy engine & session
│       ├── models.py         # User, Form, Submission models
│       ├── routers/
│       │   └── __init__.py
│       ├── static/
│       │   └── .gitkeep
│       └── templates/
│           └── .gitkeep
└── tests/
    ├── __init__.py
    ├── conftest.py           # Test DB setup, async client fixture
    └── test_health.py        # Health endpoint tests
```

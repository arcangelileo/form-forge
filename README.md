# FormForge

**Form backend-as-a-service** — Instant API endpoints for HTML forms. Point any `<form>` tag at a FormForge endpoint, and submissions are captured, stored, and forwarded via email. No server code needed.

## Features

- **Instant form endpoints** — Create endpoints in seconds, each with a unique URL
- **Dashboard** — View, search, and paginate through submissions
- **Email notifications** — Get notified when new submissions arrive
- **Spam protection** — Built-in honeypot fields and IP-based rate limiting
- **CSV export** — Download submissions as CSV with one click
- **Embeddable snippets** — Copy-paste HTML snippets for your forms
- **Custom redirects** — Send users to a thank-you page after submission
- **CORS support** — Configure allowed origins per form
- **Self-hostable** — Run on your own server with Docker

## Quick Start

### With Docker (recommended)

```bash
# Clone the repo
git clone https://github.com/arcangelileo/form-forge.git
cd form-forge

# Copy and configure environment
cp .env.example .env
# Edit .env with your secret key and SMTP settings

# Run with Docker Compose
docker compose up -d
```

The app will be available at `http://localhost:8000`.

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the app
PYTHONPATH=src uvicorn app.main:app --reload --app-dir src

# Run tests
PYTHONPATH=src pytest tests/ -v
```

## Usage

1. **Sign up** at `/register`
2. **Create a form** from the dashboard
3. **Copy the endpoint URL** (e.g., `http://localhost:8000/f/abc-123-def`)
4. **Point your HTML form** at the endpoint:

```html
<form action="http://localhost:8000/f/your-form-id" method="POST">
  <!-- Honeypot for spam protection (keep hidden) -->
  <input type="text" name="_gotcha" style="display:none">

  <input type="text" name="name" required>
  <input type="email" name="email" required>
  <textarea name="message"></textarea>
  <button type="submit">Send</button>
</form>
```

5. **View submissions** in the dashboard, export to CSV, or receive email notifications.

## Configuration

All configuration is done via environment variables (prefix: `FORMFORGE_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `FORMFORGE_SECRET_KEY` | `change-me-in-production` | JWT signing key |
| `FORMFORGE_BASE_URL` | `http://localhost:8000` | Public URL of the app |
| `FORMFORGE_DATABASE_URL` | `sqlite+aiosqlite:///./formforge.db` | Database connection string |
| `FORMFORGE_SMTP_HOST` | *(empty)* | SMTP server hostname |
| `FORMFORGE_SMTP_PORT` | `587` | SMTP server port |
| `FORMFORGE_SMTP_USER` | *(empty)* | SMTP username |
| `FORMFORGE_SMTP_PASSWORD` | *(empty)* | SMTP password |
| `FORMFORGE_SMTP_FROM_EMAIL` | `noreply@formforge.dev` | Sender email address |
| `FORMFORGE_SUBMISSIONS_PER_MINUTE` | `10` | Rate limit per form per IP |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/f/{form_uuid}` | Submit a form (public) |
| `POST` | `/api/auth/register` | Register a new account |
| `POST` | `/api/auth/login` | Log in |
| `POST` | `/api/auth/logout` | Log out |
| `GET` | `/api/auth/me` | Get current user |
| `GET` | `/api/forms/` | List your forms |
| `POST` | `/api/forms/` | Create a new form |
| `GET` | `/api/forms/{id}` | Get a form |
| `PUT` | `/api/forms/{id}` | Update a form |
| `DELETE` | `/api/forms/{id}` | Delete a form |
| `GET` | `/api/forms/{id}/submissions` | List submissions |
| `GET` | `/api/forms/{id}/export/csv` | Export submissions as CSV |

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy (async)
- **Database**: SQLite (via aiosqlite)
- **Frontend**: Jinja2 templates, Tailwind CSS (CDN)
- **Auth**: JWT tokens in httponly cookies, bcrypt password hashing
- **Email**: aiosmtplib (SMTP)

## License

MIT

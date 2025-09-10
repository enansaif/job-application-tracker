## Job Application Tracker

A lightweight API service to track job applications, including which resume version was submitted, application status, company and country data, interviews, and tags. It also stores resumes as PDF uploads and exposes an OpenAPI/Swagger UI for exploration.

### Key Features
- **Custom user model with email login** and token-based auth (DRF `TokenAuthentication`).
- **Entities**: `Country`, `Tag`, `Company`, `Resume` (PDF only), `Application`, `Interview`.
- **Per-user data isolation**: all resources are scoped to the authenticated user.
- **OpenAPI docs** with Swagger UI at `GET /api/docs/`.
- **Health check** endpoint at `GET /api/health/`.

---

## Tech Stack
- **Python 3.11**, **Django 5.2**, **Django REST Framework 3.16**
- **drf-spectacular** for API schema and Swagger UI
- **PostgreSQL 15**
- Docker/Docker Compose for local development

---

## Project Layout
```text
app/
  app/                 # Django project (settings, urls)
  auth/                # Auth endpoints (register, token, me)
  core/                # Models, admin, management commands
  main/                # Business APIs (tags, countries, companies, resumes, applications, interviews)
  manage.py
Dockerfile
docker-compose.yaml
requirements.txt
requirements.dev.txt
```

---

## Prerequisites
- Docker and Docker Compose (recommended), OR
- Local: Python 3.11, PostgreSQL 15, and a virtualenv tool.

---

## Quickstart (Docker Compose)
```bash
docker compose up --build -d

# Run DB migrations
docker compose exec app python manage.py migrate

# Create a superuser (optional, for Django admin)
docker compose exec app python manage.py createsuperuser
```

Default Postgres credentials are configured in `docker-compose.yaml`:
- `POSTGRES_DB=db`, `POSTGRES_USER=admin`, `POSTGRES_PASSWORD=admin`

The app reads DB settings from environment variables (already provided by Compose):
- `DB_NAME=db`, `DB_USER=admin`, `DB_PASSWORD=admin`, `DB_HOST=db`, `DB_PORT=5432`

Visit:
- Swagger UI: `http://localhost:8000/api/docs/`
- Schema (JSON): `http://localhost:8000/api/schema/`
- Health: `http://localhost:8000/api/health/`
- Admin: `http://localhost:8000/admin/`

Media uploads (resumes) are persisted to the `media_data` volume and mounted at `/app/media` in the container.

---

## Alternative: Local Setup (without Docker)
1) Create and activate a virtual environment, then install deps:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Configure a Postgres database and export env vars so Django can connect:
```bash
export DB_NAME=your_db
export DB_USER=your_user
export DB_PASSWORD=your_password
export DB_HOST=127.0.0.1
export DB_PORT=5432
```

3) Apply migrations and run the server:
```bash
python app/manage.py migrate
python app/manage.py runserver 0.0.0.0:8000
```

4) (Optional) Create a superuser for admin:
```bash
python app/manage.py createsuperuser
```

Note: `MEDIA_ROOT` defaults to `app/media/`. Ensure the folder exists and is writable.

---

## Authentication
This API uses DRF Token Authentication. Typical flow:
1) Register a user
2) Obtain an auth token
3) Send `Authorization: Token <token>` header in requests

### Register
`POST /api/auth/register/`
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"YourStrongP@ssw0rd","name":"User"}'
```

### Obtain Token
`POST /api/auth/token/`
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"YourStrongP@ssw0rd"}'
```
Response: `{ "token": "<token>" }`

### Current User
`GET /api/auth/me/`
```bash
curl http://localhost:8000/api/auth/me/ \
  -H 'Authorization: Token <token>'
``;
`PATCH /api/auth/me/` supports updating `name` and `password`.

---

## API Endpoints Overview
All endpoints below require `Authorization: Token <token>` unless noted.

### Tags
- `GET /api/tags/` — list tags
- `POST /api/tags/` — create tag `{ "name": "backend" }`
- `PATCH /api/tags/{id}/` — update
- `DELETE /api/tags/{id}/` — delete

### Countries
- `GET /api/country/` — list countries
- `POST /api/country/` — create `{ "name": "Germany" }`
- `PATCH /api/country/{id}/` — update
- `DELETE /api/country/{id}/` — delete

### Companies
- `GET /api/company/` — list companies
- `POST /api/company/` — create
  - Request fields: `name` (string, required), `country` (pk, optional), `link` (url, optional), `tags` (list of strings, optional)
  - Example:
```bash
curl -X POST http://localhost:8000/api/company/ \
  -H 'Authorization: Token <token>' \
  -H 'Content-Type: application/json' \
  -d '{"name":"Acme Corp","country":1,"link":"https://acme.example","tags":["backend","python"]}'
```
- `GET /api/company/{id}` — retrieve
- `PATCH /api/company/{id}` — update
- `DELETE /api/company/{id}` — delete

### Resumes (PDF only)
- `GET /api/resume/` — list resumes
- `POST /api/resume/` — upload a PDF with optional tags
  - multipart/form-data fields: `file` (PDF), `tags` (list of strings)
  - Example:
```bash
curl -X POST http://localhost:8000/api/resume/ \
  -H 'Authorization: Token <token>' \
  -F 'file=@/path/to/resume.pdf;type=application/pdf' \
  -F 'tags=ml' -F 'tags=backend'
```
- `GET /api/resume/{id}/` — retrieve
- `PATCH /api/resume/{id}/` — update file and/or tags (multipart/form-data); set empty tags list to clear

### Applications
- `POST /api/application/` — create
  - Fields: `company_id` (pk), `country_id` (pk, optional), `tag_ids` (list of pks, optional), `resume_id` (pk, optional), `position` (string), `link` (url, optional), `note` (text, optional), `status` (one of: `applied`, `interviewing`, `rejected`, `offer`, `accepted`)
  - Example:
```bash
curl -X POST http://localhost:8000/api/application/ \
  -H 'Authorization: Token <token>' \
  -H 'Content-Type: application/json' \
  -d '{
        "company_id": 1,
        "country_id": 1,
        "tag_ids": [2,3],
        "resume_id": 1,
        "position": "Senior Backend Engineer",
        "link": "https://jobs.example/apply",
        "note": "Referred by Alice",
        "status": "applied"
      }'
```
- `GET /api/application/{id}/` — retrieve
- `PATCH /api/application/{id}/` — partial update (same fields as create; `tag_ids` replaces tags if provided)

### Interviews
- `GET /api/interview/` — list interviews
- `POST /api/interview/` — create
  - Fields: `application` (pk, must belong to current user), `tags` (list of strings, optional), `date` (YYYY-MM-DD), `note` (optional)
- `GET /api/interview/{id}/` — retrieve
- `PATCH /api/interview/{id}/` — update (set empty `tags` list to clear)
- `DELETE /api/interview/{id}/` — delete

---

## OpenAPI & Swagger
- Schema: `GET /api/schema/`
- Swagger UI: `GET /api/docs/`

Note: The schema excludes the `schema` endpoint resource itself.

---

## Development

### Running Tests
Unit tests live under `app/core/tests/` and cover models and APIs.
```bash
# Docker
docker compose exec app python manage.py test

# Local
python app/manage.py test
```

### Linting
`requirements.dev.txt` includes `flake8`.
```bash
pip install -r requirements.dev.txt
flake8 app
```

---

## Troubleshooting
- Cannot connect to DB: confirm `DB_*` env vars and that Postgres is reachable.
- 401 Unauthorized: ensure you send `Authorization: Token <token>`.
- Resume upload rejected: only PDFs are allowed; content-type must be `application/pdf`, file must start with `%PDF`.
- Unique constraints: `name` must be unique per user for `Tag`, `Country`, `Company`.

---

## Security Notes
- Do not run with `DEBUG=True` in production. Configure `ALLOWED_HOSTS` properly.
- Move sensitive settings (e.g., Django `SECRET_KEY`) to environment variables in production.
- Use HTTPS and secure token storage on the client side.

---

## License
This project is licensed under the terms of the `LICENSE` file.

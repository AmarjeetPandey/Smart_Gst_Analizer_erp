# Production Setup

SmartGST uses PostgreSQL for production. The application does not contain a production database password or JWT secret; provide both through environment variables.

## Managed PostgreSQL

Copy `.env.example` to `.env` and set:

```env
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require
SECRET_KEY=<random value of at least 32 characters>
ENVIRONMENT=production
DEBUG=False
FRONTEND_URL=https://your-domain.example
CORS_ORIGINS=["https://your-domain.example"]
ALLOWED_HOSTS=["your-domain.example"]
```

On PowerShell, a suitable secret can be generated with:

```powershell
[Convert]::ToBase64String((1..48 | ForEach-Object { Get-Random -Maximum 256 }))
```

Do not commit `.env` or send database credentials through source control.

## Docker

The default Compose deployment uses the managed PostgreSQL database from `DATABASE_URL`. Set `DATABASE_URL` and `SECRET_KEY` in the root `.env`, then run from the project root:

```powershell
docker compose --env-file .env -f docker/docker-compose.yml up --build -d
```

The backend bootstraps the schema before Uvicorn starts. The bootstrap is safe to rerun for an already initialized database and does not provision a platform administrator; accounts are created through email OTP login. Nginx exposes the browser-facing API at `/api/v1`, so the frontend never attempts to resolve the internal Docker hostname `backend`.

For local development using the managed database, initialize it once from the project root, then start the backend:

```powershell
Push-Location backend
python -m scripts.bootstrap_database
python run.py
Pop-Location
```

Development startup creates tables automatically only for SQLite. PostgreSQL schema changes should go through the bootstrap step rather than being applied on every API startup.

The bundled PostgreSQL service is optional and only starts with the `local-database` profile. For local PostgreSQL, set `POSTGRES_PASSWORD`, point `DATABASE_URL` at that database, and start Compose with `--profile local-database`. The default managed-database setup does not need `POSTGRES_PASSWORD`.

Compose publishes HTTP on port 80. Terminate HTTPS at a TLS-enabled load balancer or reverse proxy before exposing the application publicly; this Nginx configuration does not provide TLS certificates.

## Local tests

The test suite uses an in-memory SQLite database and does not connect to production PostgreSQL:

```powershell
Push-Location backend
$env:PYTHONPATH=(Get-Location).Path
pytest -q
Pop-Location
```

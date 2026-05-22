# Secure Secrets Manager

A Flask-based REST API for securely storing, retrieving, and sharing sensitive credentials such as API keys and passwords. All secret values are encrypted at rest using Fernet symmetric encryption. Access is strictly owner-scoped, and secrets can be shared via one-time expiring tokens.

---

## Features

- **Encrypted storage** — secret values are encrypted with Fernet (AES-128-CBC + HMAC) before being written to disk; the plaintext never touches the filesystem
- **JWT authentication** — stateless token-based auth with configurable expiry
- **Strict access control** — users can only read, update, or delete their own secrets
- **One-time share links** — generate a token that grants a single read of a secret to anyone; the token is invalidated immediately after use or upon expiry
- **Audit log** — every significant event (login, create, access, share) is appended to `data/audit.log` as a JSON line; secret values are never logged
- **Rate limiting** — 10 requests/minute on auth endpoints, 100 requests/hour globally
- **File-based storage** — no database required; state lives in `data/` as JSON files

---

## Installation

### Prerequisites

- Python 3.10 or later

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd secure-secrets-manager
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and edit it:

```bash
# Windows
copy env.example .env

# macOS / Linux
cp env.example .env
```

Open `.env` and set at minimum:

```dotenv
SECRET_KEY=replace-with-a-long-random-string
JWT_SECRET=replace-with-another-random-string

# Generate a Fernet key (run once, then paste the output below):
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_KEY=
```

> **Important:** If `FERNET_KEY` is left blank the server generates one automatically on first
> start and appends it to `.env`. Back it up — if it is lost, all stored secrets become
> unrecoverable.

### 5. Run the development server

```bash
python app.py
```

The API is now available at `http://localhost:5000`.

---

## API Endpoints

| Method | Endpoint | Auth required | Description |
|--------|----------|:---:|-------------|
| `POST` | `/register` | No | Create a new user account |
| `POST` | `/login` | No | Authenticate and receive a JWT |
| `POST` | `/secrets` | Yes | Store a new encrypted secret |
| `GET` | `/secrets` | Yes | List all secrets owned by the caller |
| `GET` | `/secrets/<id>` | Yes | Retrieve and decrypt a secret |
| `PUT` | `/secrets/<id>` | Yes | Update a secret's metadata |
| `DELETE` | `/secrets/<id>` | Yes | Delete a secret |
| `POST` | `/secrets/<id>/share` | Yes | Generate a one-time share token |
| `GET` | `/share/<token>` | No | Access a secret via share token |

All authenticated endpoints require the header:

```
Authorization: Bearer <token>
```

---

## Usage Examples

The examples below use `curl`. Replace `TOKEN` with the JWT returned by `/login`.

### Register a user

```bash
curl -s -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "supersecret123"}'
```

```json
{
  "message": "User registered",
  "user": {
    "id": "a1b2c3d4-...",
    "username": "alice",
    "created_at": "2026-05-22T10:00:00+00:00"
  }
}
```

### Log in

```bash
curl -s -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "supersecret123"}'
```

```json
{ "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." }
```

### Store a secret

```bash
curl -s -X POST http://localhost:5000/secrets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "name": "STRIPE_API_KEY",
    "value": "sk_live_abc123...",
    "description": "Production Stripe key",
    "tags": ["payments", "production"]
  }'
```

```json
{
  "message": "Secret stored",
  "secret": {
    "id": "f7e6d5c4-...",
    "name": "STRIPE_API_KEY",
    "description": "Production Stripe key",
    "tags": ["payments", "production"],
    "created_at": "2026-05-22T10:01:00+00:00",
    "updated_at": "2026-05-22T10:01:00+00:00"
  }
}
```

### List secrets

```bash
curl -s http://localhost:5000/secrets \
  -H "Authorization: Bearer TOKEN"
```

```json
{
  "secrets": [
    {
      "id": "f7e6d5c4-...",
      "name": "STRIPE_API_KEY",
      "description": "Production Stripe key",
      "tags": ["payments", "production"],
      "created_at": "2026-05-22T10:01:00+00:00",
      "updated_at": "2026-05-22T10:01:00+00:00"
    }
  ]
}
```

### Retrieve a secret (decrypted)

```bash
curl -s http://localhost:5000/secrets/f7e6d5c4-... \
  -H "Authorization: Bearer TOKEN"
```

```json
{
  "id": "f7e6d5c4-...",
  "name": "STRIPE_API_KEY",
  "value": "sk_live_abc123...",
  "description": "Production Stripe key",
  "tags": ["payments", "production"],
  "created_at": "2026-05-22T10:01:00+00:00",
  "updated_at": "2026-05-22T10:01:00+00:00"
}
```

### Update secret metadata

```bash
curl -s -X PUT http://localhost:5000/secrets/f7e6d5c4-... \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"description": "Production Stripe key (rotate by 2026-12-01)", "tags": ["payments", "production", "rotate"]}'
```

```json
{
  "message": "Secret updated",
  "secret": { "...": "..." }
}
```

### Delete a secret

```bash
curl -s -X DELETE http://localhost:5000/secrets/f7e6d5c4-... \
  -H "Authorization: Bearer TOKEN"
```

```json
{ "message": "Secret deleted" }
```

### Generate a one-time share link

```bash
curl -s -X POST http://localhost:5000/secrets/f7e6d5c4-.../share \
  -H "Authorization: Bearer TOKEN"
```

```json
{
  "token": "X9zQ2mR7kL...",
  "expires_at": "2026-05-22T11:01:00+00:00"
}
```

### Access a secret via share token (no auth required)

```bash
curl -s http://localhost:5000/share/X9zQ2mR7kL...
```

```json
{
  "name": "STRIPE_API_KEY",
  "value": "sk_live_abc123...",
  "description": "Production Stripe key"
}
```

Accessing the same token a second time returns:

```json
{ "error": "Token has already been used" }
```

---

## Running Tests

```bash
pytest tests/ -v
```

All 17 tests should pass. Tests use an isolated temporary directory so they never touch your `data/` folder.

---

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | `development`, `production`, or `testing` |
| `SECRET_KEY` | *(insecure default)* | Flask session signing key |
| `JWT_SECRET` | *(insecure default)* | JWT signing secret |
| `JWT_EXPIRY_HOURS` | `24` | How long a JWT remains valid |
| `FERNET_KEY` | *(auto-generated)* | Base64-encoded 32-byte Fernet key |
| `DATA_DIR` | `data/` | Directory for all file-based storage |
| `SHARE_TOKEN_EXPIRY_MINUTES` | `60` | Lifetime of a share token in minutes |
| `RATELIMIT_DEFAULT` | `100 per hour` | Global rate limit |
| `RATELIMIT_STORAGE_URI` | `memory://` | Flask-Limiter backend URI |

---

## Security Notes

- Never commit `.env` or the `data/` directory to version control.
- In production set `FLASK_ENV=production` and use a proper WSGI server (e.g. Gunicorn).
- The `FERNET_KEY` is the single point of trust for all encrypted secrets — store it in a secrets manager (e.g. AWS Secrets Manager, HashiCorp Vault) for production use.
- Rate limiting defaults to in-memory storage; for multi-process deployments set `RATELIMIT_STORAGE_URI` to a Redis URI.

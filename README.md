# Kisan AI — Django API

Hindi crop advisory API with semantic search and offline voice STT.
Migrated from FastAPI to Django for admin panel and long-term maintainability.

## Project Structure

```
KisanAPI/                          ← project root (run everything from here)
├── manage.py
├── requirements.txt
├── Procfile
├── render.yaml
├── .env.example                   ← copy to .env and fill in values
├── chatbot.html                   ← frontend UI (unchanged)
├── services.py                    ← business logic (Django-adapted)
├── embedding_service.py           ← sentence-transformers singleton (unchanged)
├── voice_service.py               ← Vosk STT singleton (unchanged)
│
├── kisan/                         ← Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── api/                           ← Django app
│   ├── models.py                  ← Solution model (managed=False, existing table)
│   ├── serializers.py
│   ├── views.py                   ← all endpoints
│   ├── urls.py
│   ├── admin.py                   ← full admin panel
│   ├── apps.py                    ← ML model loading on startup
│   └── exceptions.py
│
└── templates/
    └── admin/
        └── index.html             ← dashboard stats widget
```

## Quick Start

```bash
# 1. Create & activate venv
py -3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# if failed try:
pip install torch==2.6.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL and DJANGO_SECRET_KEY

# 4. SECRET_KEY:
python -c "import secrets; print(secrets.token_urlsafe(50))"

# 5. Verify database connection:
python manage.py dbshell

# 6. Run migrations (Django creates auth/session/admin tables only;
#    your existing 'solutions' table is untouched because managed=False)
python manage.py migrate

# 7. Enable pgvector & create the similarity index
(Invoke-WebRequest -Uri http://localhost:8000/init-db -Method POST).Content

# 8. Create admin superuser
python manage.py createsuperuser

# 9. Run dev server
python manage.py runserver
```

> **Windows note:** The sentence-transformers model is cached locally in
> `.cache/` inside the project folder (avoids Windows symlink restrictions).
> The model (~470 MB) downloads automatically on first startup.
> Download the Vosk Hindi model separately:
> https://alphacephei.com/vosk/models → `vosk-model-small-hi-0.22.zip`
> and extract it to the project root.

Visit `http://localhost:8000/` for the chatbot UI.
Visit `http://localhost:8000/admin/` for the admin panel.

## API Endpoints

| Method | Path                   | Description                              |
| ------ | ---------------------- | ---------------------------------------- |
| GET    | `/`                    | Serve chatbot HTML                       |
| GET    | `/health`              | Liveness + readiness check               |
| POST   | `/init-db`             | Enable pgvector extension + create index |
| POST   | `/generate-embeddings` | Backfill missing embeddings              |
| GET    | `/all`                 | All records (no filter)                  |
| GET    | `/search?q=<query>`    | Top-10 semantic results                  |
| POST   | `/search`              | Top-1 result (chatbot mode)              |
| POST   | `/voice`               | WAV → Hindi transcript                   |
| POST   | `/voice-search`        | WAV → transcript → crop solution         |

## Admin Panel

After creating a superuser, log in at `/admin/`:

- **Dashboard** — record count, embedding coverage, top crops
- **Solutions** — search, filter, edit 1500+ records
- **Bulk actions**:
  - Generate embeddings for selected records
  - Export selected to CSV (Excel-compatible UTF-8-BOM)
- **Auto-embedding** — changing `problem` or `cropname` in the detail view
  regenerates the embedding automatically on save

## Production Deployment (Render)

```bash
# 1. Push code to GitHub
# 2. Create a new Web Service on Render pointing to your repo
# 3. Render reads render.yaml automatically
# 4. Add environment variables in the Render dashboard:
#      DATABASE_URL  (from your Render PostgreSQL database)
#      DJANGO_SECRET_KEY
```

## Environment Variables

| Variable                  | Required | Default          | Description                              |
| ------------------------- | -------- | ---------------- | ---------------------------------------- |
| `DATABASE_URL`            | ✅       | —                | PostgreSQL connection string             |
| `DJANGO_SECRET_KEY`       | ✅       | insecure default | Django secret key (change in production) |
| `DEBUG`                   | —        | `False`          | Enable Django debug mode                 |
| `ALLOWED_HOSTS`           | —        | `*`              | Comma-separated allowed hosts            |
| `DISABLE_EMBEDDINGS`      | —        | `false`          | Skip embedding model (keyword-only)      |
| `CACHE_DIR`               | —        | `~/.cache/...`   | Sentence-transformers cache directory    |
| `VOSK_MODEL_PATH`         | —        | auto-detect      | Override Vosk model location             |
| `MAX_CONCURRENT_REQUESTS` | —        | `10`             | Max simultaneous voice requests          |

## Migration Notes

### What changed from FastAPI

| File                   | Status       | Notes                                             |
| ---------------------- | ------------ | ------------------------------------------------- |
| `embedding_service.py` | ✅ Unchanged | Standalone singleton                              |
| `voice_service.py`     | ✅ Unchanged | Standalone singleton                              |
| `chatbot.html`         | ✅ Unchanged | Pure HTML/JS                                      |
| `services.py`          | 🔄 Adapted   | SQLAlchemy Session → Django `connection.cursor()` |
| `models.py`            | 🔄 Replaced  | SQLAlchemy → Django ORM (`managed=False`)         |
| `schema.py`            | 🔄 Replaced  | Pydantic → DRF Serializers                        |
| `main.py`              | 🔄 Replaced  | FastAPI → Django views + urls                     |
| `db.py`                | 🔄 Replaced  | SQLAlchemy engine → Django `settings.DATABASES`   |

### Database

The existing `solutions` table is **not touched** by Django migrations (`managed = False`).
Run `python manage.py migrate` only to create Django's internal tables
(auth, sessions, admin, contenttypes).

To enable pgvector and create the similarity index on a fresh database:

```
POST /init-db
```

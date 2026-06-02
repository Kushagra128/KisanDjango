# Kisan AI — Django API

Hindi crop advisory API with semantic search and offline voice STT.
Migrated from FastAPI to Django for admin panel and long-term maintainability.

## Project Structure

```
KisanDjango/                       ← project root (run everything from here)
├── manage.py
├── requirements.txt
├── Procfile
├── render.yaml
├── .env.example                   ← copy to .env and fill in values
├── chatbot.html                   ← standalone chatbot UI
├── services.py                    ← business logic (Django-adapted)
├── embedding_service.py           ← sentence-transformers singleton
├── voice_service.py               ← Vosk STT singleton
│
├── static/                        ← project-level static files
│   └── kisan-widget.js            ← embeddable chatbot widget (one <script> tag)
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

---

## Quick Start

```bash
# 1. Create & activate venv
py -3.12 -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / Mac

# 2. Install dependencies
pip install -r requirements.txt

# If torch install fails, run this first then retry:
pip install torch==2.6.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env          # Windows
# cp .env.example .env          # Linux / Mac
# Edit .env — set DATABASE_URL and DJANGO_SECRET_KEY

# 4. Generate a secure SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(50))"

# 5. Verify database connection
python manage.py dbshell

# 6. Run migrations
#    Django creates auth/session/admin tables only.
#    Your existing 'solutions' table is untouched (managed=False).
python manage.py migrate

# 7. Enable pgvector & create the similarity index
#    PowerShell:
(Invoke-WebRequest -Uri http://localhost:8000/init-db -Method POST).Content
#    curl (Linux / Mac):
# curl -X POST http://localhost:8000/init-db

# 8. Create admin superuser
python manage.py createsuperuser

# 9. Run dev server
python manage.py runserver
```

> **Windows note:** The sentence-transformers model (~470 MB) downloads
> automatically on first startup and is cached in `.cache/` inside the
> project folder — this avoids Windows symlink restrictions.
>
> The Vosk Hindi model must be downloaded separately:
> <https://alphacephei.com/vosk/models> → download `vosk-model-small-hi-0.22.zip`
> and extract it to the project root so the folder
> `KisanDjango/vosk-model-small-hi-0.22/` exists.

Visit `http://localhost:8000/` for the chatbot UI.  
Visit `http://localhost:8000/admin/` for the admin panel.

---

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

---

## Embeddable Chatbot Widget

`static/kisan-widget.js` is a self-contained embeddable widget.  
Drop **one `<script>` tag** into any HTML page and the किसान AI chatbot appears — no extra CSS, no framework, no build step.

### Basic embed

Add this line before the closing `</body>` tag of any HTML file:

```html
<script
	src="http://localhost:8000/static/kisan-widget.js"
	data-api="http://localhost:8000"
></script>
```

### Full example — a completely separate website

```html
<!DOCTYPE html>
<html lang="en">
	<head>
		<meta charset="UTF-8" />
		<title>My Farm Website</title>
	</head>
	<body>
		<h1>Welcome to My Farm</h1>
		<p>We grow wheat, tomatoes and mangoes.</p>

		<!-- Kisan AI widget — just this one line -->
		<script
			src="http://localhost:8000/static/kisan-widget.js"
			data-api="http://localhost:8000"
		></script>
	</body>
</html>
```

Open that file in a browser while your Django server is running — the 🌾 button appears in the bottom-right corner.

### Configuration attributes

| Attribute       | Required | Default        | Description                             |
| --------------- | -------- | -------------- | --------------------------------------- |
| `data-api`      | ✅       | auto-detect    | Base URL of your Kisan AI Django server |
| `data-position` | —        | `bottom-right` | `bottom-right` or `bottom-left`         |

```html
<!-- Place widget on the left side -->
<script
	src="http://localhost:8000/static/kisan-widget.js"
	data-api="http://localhost:8000"
	data-position="bottom-left"
></script>
```

### How it works

- **Shadow DOM** — widget CSS is fully isolated; it cannot conflict with the host page's styles and vice versa
- **Single file** — all HTML, CSS, and JS are bundled inside `kisan-widget.js`
- **Double-init guard** — safe to include on pages that load the script more than once
- **Voice input** — uses browser `SpeechRecognition` (Chrome/Edge) or falls back to server-side Vosk

---

## Using the Widget on a Hosted / Production Server

When your Django project is deployed (e.g. on Render at
`https://kisan-ai-django.onrender.com`), update the following:

### 1. `ALLOWED_HOSTS` in `.env`

Add your live domain:

```env
ALLOWED_HOSTS=kisan-ai-django.onrender.com,yourdomain.com
```

### 2. The `<script>` tag on every site that embeds the widget

Replace `localhost:8000` with your live domain in **both** `src` and `data-api`:

```html
<!-- Local dev -->
<script
	src="http://localhost:8000/static/kisan-widget.js"
	data-api="http://localhost:8000"
></script>

<!-- Production -->
<script
	src="https://kisan-ai-django.onrender.com/static/kisan-widget.js"
	data-api="https://kisan-ai-django.onrender.com"
></script>
```

### 3. CORS — already handled

`settings.py` has `CORS_ALLOW_ALL_ORIGINS = True` so the widget loads from
any domain. In production you can restrict it to specific domains:

```python
# kisan/settings.py
# Replace CORS_ALLOW_ALL_ORIGINS = True with:
CORS_ALLOWED_ORIGINS = [
    "https://yourfarmwebsite.com",
    "https://anotherclient.com",
]
```

### 4. Static files — already automated

`render.yaml` runs `python manage.py collectstatic --noinput` on every
deploy, so WhiteNoise serves `kisan-widget.js` at `/static/kisan-widget.js`
automatically. No manual step needed on Render.

### Checklist before going live

| What                    | File / Location                   | Change                                                |
| ----------------------- | --------------------------------- | ----------------------------------------------------- |
| Allowed hosts           | `.env`                            | Add your domain to `ALLOWED_HOSTS`                    |
| Widget `src`            | Every HTML that embeds the widget | `src="https://yourdomain.com/static/kisan-widget.js"` |
| Widget `data-api`       | Every HTML that embeds the widget | `data-api="https://yourdomain.com"`                   |
| Static files            | Automatic                         | `render.yaml` already runs `collectstatic`            |
| CORS (optional tighten) | `kisan/settings.py`               | Replace `CORS_ALLOW_ALL_ORIGINS` with allowed list    |

---

## Admin Panel

After creating a superuser, log in at `/admin/`:

- **Dashboard** — record count, embedding coverage, top crops
- **Solutions** — search, filter, and edit 1500+ records
- **Bulk actions**:
  - Generate embeddings for selected records
  - Export selected records to CSV (Excel-compatible UTF-8-BOM)
- **Auto-embedding** — changing `problem` or `cropname` in the detail view
  regenerates the embedding automatically on save

---

## Production Deployment (Render)

1. Push code to GitHub
2. Create a new **Web Service** on Render pointing to your repo
3. Render reads `render.yaml` automatically
4. Add environment variables in the Render dashboard:
   - `DATABASE_URL` — from your Render PostgreSQL database
   - `DJANGO_SECRET_KEY` — generate with `secrets.token_urlsafe(50)`
5. After first deploy, run:
   ```
   POST /init-db
   ```
   to enable the pgvector extension and create the similarity index.

---

## Environment Variables

| Variable                  | Required | Default              | Description                              |
| ------------------------- | -------- | -------------------- | ---------------------------------------- |
| `DATABASE_URL`            | ✅       | —                    | PostgreSQL connection string             |
| `DJANGO_SECRET_KEY`       | ✅       | insecure default     | Django secret key (change in production) |
| `DEBUG`                   | —        | `False`              | Set `True` for local development         |
| `ALLOWED_HOSTS`           | —        | `*`                  | Comma-separated allowed hosts            |
| `DISABLE_EMBEDDINGS`      | —        | `false`              | Set `true` to skip embedding model       |
| `CACHE_DIR`               | —        | `.cache/` in project | Sentence-transformers cache directory    |
| `VOSK_MODEL_PATH`         | —        | auto-detect          | Override Vosk model folder location      |
| `MAX_CONCURRENT_REQUESTS` | —        | `10`                 | Max simultaneous voice requests          |

---

## Migration Notes

### What changed from FastAPI

| File                   | Status      | Notes                                             |
| ---------------------- | ----------- | ------------------------------------------------- |
| `embedding_service.py` | ✅ Kept     | Standalone singleton, Windows cache fix applied   |
| `voice_service.py`     | ✅ Kept     | Standalone singleton                              |
| `chatbot.html`         | ✅ Kept     | Pure HTML/JS, unchanged                           |
| `services.py`          | 🔄 Adapted  | SQLAlchemy Session → Django `connection.cursor()` |
| `models.py`            | 🔄 Replaced | SQLAlchemy → Django ORM (`managed=False`)         |
| `schema.py`            | 🔄 Replaced | Pydantic → DRF Serializers                        |
| `main.py`              | 🔄 Replaced | FastAPI → Django views + urls                     |
| `db.py`                | 🔄 Replaced | SQLAlchemy engine → Django `settings.DATABASES`   |

### Database

The existing `solutions` table is **not touched** by Django migrations
(`managed = False`). Run `python manage.py migrate` only to create Django's
internal tables (auth, sessions, admin, contenttypes).

To enable pgvector and create the similarity index on a fresh database:

```
POST /init-db
```

# Kisan AI — Complete Technical Documentation

> Hindi crop advisory chatbot API with semantic search, offline voice STT, and embeddable widget.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Data Flow Diagram](#3-data-flow-diagram)
4. [Use Case Diagram](#4-use-case-diagram)
5. [Entity Relationship Diagram](#5-entity-relationship-diagram)
6. [Sequence Diagrams](#6-sequence-diagrams)
7. [Component Diagram](#7-component-diagram)
8. [Tech Stack](#8-tech-stack)
9. [ML Models](#9-ml-models)
10. [Search Algorithm](#10-search-algorithm)
11. [API Endpoints](#11-api-endpoints)
12. [Database Schema](#12-database-schema)
13. [Embeddable Widget](#13-embeddable-widget)
14. [Admin Panel](#14-admin-panel)
15. [Deployment Architecture](#15-deployment-architecture)
16. [Design Patterns](#16-design-patterns)
17. [Environment Variables](#17-environment-variables)
18. [File Structure](#18-file-structure)
19. [Known Issues & Fixes](#19-known-issues--fixes)

---

## 1. Project Overview

**Kisan AI** is a Hindi-language crop advisory system that helps Indian farmers diagnose crop diseases and get treatment solutions. Farmers can type or speak their problem in Hindi or English, and the system returns the most relevant solution from a database of 1500+ crop problem–solution pairs.

| Property                 | Value                                      |
| ------------------------ | ------------------------------------------ |
| Language                 | Python 3.12                                |
| Framework                | Django 5.0.6                               |
| Database                 | PostgreSQL + pgvector                      |
| Primary language support | Hindi + English                            |
| Embedding dimensions     | 384                                        |
| Number of crop solutions | 1500+                                      |
| Voice support            | Offline Hindi STT (Vosk)                   |
| Deployment               | Render.com                                 |
| Repository               | https://github.com/Kushagra128/KisanDjango |

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  chatbot.html    │  │  kisan-widget.js  │  │  Any Website     │  │
│  │  (standalone UI) │  │  (Shadow DOM)     │  │  + <script> tag  │  │
│  └────────┬─────────┘  └────────┬──────────┘  └────────┬─────────┘  │
│           │                     │                       │            │
└───────────┼─────────────────────┼───────────────────────┼────────────┘
            │  HTTP / REST        │                       │
            ▼                     ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DJANGO API SERVER                             │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    URL Router (urls.py)                      │    │
│  │  / │ /health │ /search │ /voice │ /voice-search │ /docs/    │    │
│  └───────────────────────┬─────────────────────────────────────┘    │
│                          │                                           │
│  ┌───────────────────────▼─────────────────────────────────────┐    │
│  │                   DRF Views (views.py)                       │    │
│  │  ChatbotView │ SearchView │ VoiceView │ VoiceSearchView      │    │
│  └──────┬──────────────┬──────────────────────┬────────────────┘    │
│         │              │                      │                      │
│         ▼              ▼                      ▼                      │
│  ┌────────────┐ ┌─────────────────┐ ┌─────────────────┐            │
│  │ services.py│ │embedding_service│ │  voice_service  │            │
│  │            │ │    .py          │ │     .py         │            │
│  │ detect_crop│ │ SentenceTrans-  │ │  Vosk Kaldi     │            │
│  │ hybrid_    │ │ formers Model   │ │  Hindi STT      │            │
│  │ search     │ │ (384-dim)       │ │                 │            │
│  └──────┬─────┘ └────────┬────────┘ └─────────────────┘            │
│         │                │                                           │
└─────────┼────────────────┼───────────────────────────────────────────┘
          │                │ embeddings
          ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     POSTGRESQL DATABASE                              │
│                                                                      │
│   solutions table                                                    │
│   ┌──────────┬──────────┬──────────┬──────────────────────────┐    │
│   │ id (PK)  │ cropname │ problem  │ embedding (vector 384)    │    │
│   │          │          │          │ solution                  │    │
│   └──────────┴──────────┴──────────┴──────────────────────────┘    │
│                                                                      │
│   pgvector IVFFLAT index on embedding (cosine ops, 100 lists)       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow Diagram

### Level 0 — Context Diagram

```
                    ┌─────────────────────────────┐
                    │                             │
   [Farmer] ──────► │       KISAN AI SYSTEM       │ ──────► [Crop Solution]
      text/voice    │                             │
                    └─────────────────────────────┘
                                  │
                          reads/writes
                                  │
                    ┌─────────────▼───────────────┐
                    │      PostgreSQL DB           │
                    │   (solutions + embeddings)   │
                    └─────────────────────────────┘
```

### Level 1 — Text Search Flow

```
  User Query (Hindi/English)
         │
         ▼
  ┌─────────────────┐
  │  detect_crop()  │  ← CROP_ALIASES dict (200+ crops)
  │  token matching │
  └────────┬────────┘
           │ detected_crop (or None)
           ▼
  ┌─────────────────────────────┐
  │   generate_embedding()      │  ← SentenceTransformer
  │   paraphrase-multilingual   │    384-dim vector
  │   MiniLM-L12-v2             │
  └────────┬────────────────────┘
           │ query_vector [384 floats]
           ▼
  ┌─────────────────────────────┐
  │   pgvector cosine search    │  ← PostgreSQL
  │   top-50 candidates         │    1 - (embedding <=> query)
  │   threshold ≥ 0.2           │    filtered by cropname
  └────────┬────────────────────┘
           │ 50 candidate rows
           ▼
  ┌─────────────────────────────┐
  │   keyword_boost()           │  ← SYMPTOM_KEYWORDS (21 categories)
  │   +0.30 per matching cat    │    Hindi + English keywords
  │   max boost = 0.90          │
  └────────┬────────────────────┘
           │ re-ranked scores
           ▼
  ┌─────────────────────────────┐
  │   sort by final_score DESC  │
  │   return top-10             │
  └────────┬────────────────────┘
           │
           ▼
      JSON Response
  [{id, cropname, problem,
    solution, similarity_score,
    search_method, detected_crop}]
```

### Level 1 — Voice Search Flow

```
  WAV Audio File (browser mic)
         │
         ▼
  ┌─────────────────┐
  │  VoiceService   │  ← Vosk vosk-model-small-hi-0.22
  │  transcribe()   │    KaldiRecognizer (per-thread)
  │  Hindi STT      │
  └────────┬────────┘
           │ Hindi transcript text
           ▼
     [Text Search Flow above]
           │
           ▼
  {transcript, result: {...}}
```

---

## 4. Use Case Diagram

```
                        KISAN AI SYSTEM
  ┌──────────────────────────────────────────────────────────────┐
  │                                                              │
  │   ┌─────────────────────────────────────────────────────┐   │
  │   │              Farmer (Primary Actor)                  │   │
  │   └──────────────────────┬──────────────────────────────┘   │
  │                          │                                   │
  │          ┌───────────────┼───────────────────┐              │
  │          │               │                   │              │
  │          ▼               ▼                   ▼              │
  │   ┌────────────┐  ┌────────────┐   ┌──────────────────┐    │
  │   │  UC-01     │  │  UC-02     │   │  UC-03           │    │
  │   │ Type query │  │ Voice query│   │ Use quick chips  │    │
  │   │ in Hindi/  │  │ (Hindi STT)│   │ (pre-filled      │    │
  │   │ English    │  │            │   │  questions)      │    │
  │   └─────┬──────┘  └─────┬──────┘   └────────┬─────────┘    │
  │         │               │                    │              │
  │         └───────────────┴────────────────────┘              │
  │                         │                                   │
  │                         ▼                                   │
  │                  ┌────────────┐                             │
  │                  │  UC-04     │                             │
  │                  │ Get crop   │                             │
  │                  │ solution   │                             │
  │                  └────────────┘                             │
  │                                                              │
  │   ┌──────────────────────────────────────────────────────┐  │
  │   │              Admin (Secondary Actor)                  │  │
  │   └────────────────────┬─────────────────────────────────┘  │
  │                        │                                     │
  │       ┌────────────────┼────────────────────┐               │
  │       │                │                    │               │
  │       ▼                ▼                    ▼               │
  │  ┌─────────┐   ┌──────────────┐   ┌──────────────────┐     │
  │  │ UC-05   │   │  UC-06       │   │  UC-07           │     │
  │  │ Manage  │   │ Generate     │   │  Export CSV      │     │
  │  │ solution│   │ embeddings   │   │                  │     │
  │  │ records │   │ (bulk)       │   │                  │     │
  │  └─────────┘   └──────────────┘   └──────────────────┘     │
  │                                                              │
  │   ┌──────────────────────────────────────────────────────┐  │
  │   │           Developer (External Actor)                  │  │
  │   └────────────────────┬─────────────────────────────────┘  │
  │                        │                                     │
  │         ┌──────────────┼───────────────┐                    │
  │         │              │               │                    │
  │         ▼              ▼               ▼                    │
  │   ┌──────────┐  ┌────────────┐  ┌──────────────┐           │
  │   │  UC-08   │  │  UC-09     │  │  UC-10       │           │
  │   │ Embed    │  │ Init DB /  │  │  View API    │           │
  │   │ widget   │  │ Gen embeds │  │  docs /docs/ │           │
  │   │ <script> │  │ via API    │  │              │           │
  │   └──────────┘  └────────────┘  └──────────────┘           │
  │                                                              │
  └──────────────────────────────────────────────────────────────┘
```

---

## 5. Entity Relationship Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        solutions                              │
├──────────────┬───────────────────────────────────────────────┤
│ id           │ INTEGER  PRIMARY KEY  AUTO INCREMENT           │
│ cropname     │ VARCHAR(500)  NOT NULL  INDEX                  │
│ problem      │ TEXT  NOT NULL                                 │
│ solution     │ TEXT  NOT NULL                                 │
│ embedding    │ VECTOR(384)  NULLABLE                          │
└──────────────┴───────────────────────────────────────────────┘
        │
        │  IVFFLAT INDEX
        │  solutions_embedding_idx
        │  USING ivfflat (embedding vector_cosine_ops)
        │  WITH (lists = 100)
        │
        ▼
  [Fast approximate nearest-neighbour search]


┌──────────────────────────────────────────────────────────────┐
│                   django_auth_user                            │
├──────────────┬───────────────────────────────────────────────┤
│ id           │ INTEGER  PRIMARY KEY                           │
│ username     │ VARCHAR  UNIQUE                                │
│ password     │ VARCHAR  (hashed)                              │
│ is_staff     │ BOOLEAN                                        │
│ is_superuser │ BOOLEAN                                        │
└──────────────┴───────────────────────────────────────────────┘
        │
        │  1 ──── * (admin session)
        ▼
┌──────────────────────────────────────────────────────────────┐
│                   django_session                              │
├──────────────┬───────────────────────────────────────────────┤
│ session_key  │ VARCHAR  PRIMARY KEY                           │
│ session_data │ TEXT                                           │
│ expire_date  │ DATETIME                                       │
└──────────────┴───────────────────────────────────────────────┘

Note: Only the `solutions` table holds domain data.
      Django auth/session tables are internal infrastructure.
      solutions is managed=False — Django migrations do not own it.
```

---

## 6. Sequence Diagrams

### 6.1 Text Search — GET /search?q=...

```
Browser          Django Router     SearchView       services.py      PostgreSQL
   │                  │                │                 │                │
   │ GET /search?q=   │                │                 │                │
   │ टमाटर में कीड़े  │                │                 │                │
   │─────────────────►│                │                 │                │
   │                  │─── route ─────►│                 │                │
   │                  │                │                 │                │
   │                  │                │─ detect_crop() ►│                │
   │                  │                │                 │─ match aliases │
   │                  │                │◄─ "टमाटर" ──────│                │
   │                  │                │                 │                │
   │                  │                │─ search_crop_solution() ────────►│
   │                  │                │                 │                │
   │                  │                │                 │─ embed query ──┤
   │                  │                │                 │  [384 floats]  │
   │                  │                │                 │                │
   │                  │                │                 │─ pgvector SQL ►│
   │                  │                │                 │  cosine search │
   │                  │                │                 │◄─ 50 rows ─────│
   │                  │                │                 │                │
   │                  │                │                 │─ keyword_boost │
   │                  │                │                 │  re-rank top10 │
   │                  │                │◄─ [results] ────│                │
   │                  │                │                 │                │
   │◄─────────────────────────────────│                 │                │
   │  JSON [{id,cropname,problem,     │                 │                │
   │         solution,score,...}]      │                 │                │
```

### 6.2 Voice Search — POST /voice-search

```
Browser        VoiceSearchView    VoiceService     services.py     PostgreSQL
   │                 │                 │                │               │
   │ POST /voice-    │                 │                │               │
   │ search          │                 │                │               │
   │ (WAV file)      │                 │                │               │
   │────────────────►│                 │                │               │
   │                 │─ transcribe() ─►│                │               │
   │                 │                 │─ KaldiRecog.   │               │
   │                 │                 │  decode WAV    │               │
   │                 │◄─ "टमाटर में..." │                │               │
   │                 │                 │                │               │
   │                 │─ detect_crop() ──────────────── ►│               │
   │                 │◄─ "टमाटर" ────────────────────── │               │
   │                 │                 │                │               │
   │                 │─ search() ───────────────────────►───────────────►
   │                 │◄─ results ──────────────────────────────────────◄│
   │                 │                 │                │               │
   │◄────────────────│                 │                │               │
   │ {transcript,    │                 │                │               │
   │  result:{...}}  │                 │                │               │
```

### 6.3 Widget Embed — any third-party website

```
ThirdPartyPage      Browser            kisan-widget.js    Django API
      │                 │                     │                │
      │ load page       │                     │                │
      │────────────────►│                     │                │
      │                 │ fetch script        │                │
      │                 │────────────────────►│                │
      │                 │◄── IIFE executes ───│                │
      │                 │                     │                │
      │                 │ attachShadow()       │                │
      │                 │ inject CSS + HTML    │                │
      │                 │ 🌾 button appears    │                │
      │                 │                     │                │
      │  user clicks 🌾 │                     │                │
      │────────────────►│                     │                │
      │                 │ widget opens         │                │
      │                 │                     │                │
      │  user types query                      │                │
      │────────────────►│                     │                │
      │                 │ fetch /search?q=... ────────────────►│
      │                 │◄── JSON results ──────────────────── │
      │                 │ typewriter animation │                │
      │◄────────────────│                     │                │
```

---

## 7. Component Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        KisanDjango Project                            │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                      kisan/ (Django Config)                   │    │
│  │   settings.py ─── urls.py ─── wsgi.py                        │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                               │                                        │
│               ┌───────────────┼───────────────┐                       │
│               ▼               ▼               ▼                       │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────────┐    │
│  │   api/ (App)    │  │  services.py │  │  static/             │    │
│  │                 │  │              │  │  kisan-widget.js     │    │
│  │  views.py       │  │  detect_crop │  │  (Shadow DOM IIFE)   │    │
│  │  urls.py        │  │  hybrid_     │  └──────────────────────┘    │
│  │  models.py      │  │  search      │                               │
│  │  admin.py       │  │  keyword_    │  ┌──────────────────────┐    │
│  │  apps.py        │  │  boost       │  │  templates/          │    │
│  │  serializers.py │  └──────────────┘  │  admin/index.html    │    │
│  │  exceptions.py  │         │          └──────────────────────┘    │
│  └─────────────────┘         │                                        │
│         │                    │                                        │
│         ▼                    ▼                                        │
│  ┌──────────────────────────────────────────┐                        │
│  │           Singleton Services             │                        │
│  │                                          │                        │
│  │  ┌───────────────────┐  ┌─────────────┐ │                        │
│  │  │ embedding_service │  │voice_service│ │                        │
│  │  │ .py               │  │.py          │ │                        │
│  │  │                   │  │             │ │                        │
│  │  │ EmbeddingGenerator│  │VoiceService │ │                        │
│  │  │ _load_lock        │  │_load_lock   │ │                        │
│  │  │ _infer_lock       │  │KaldiRecog.  │ │                        │
│  │  └────────┬──────────┘  └──────┬──────┘ │                        │
│  └───────────┼────────────────────┼─────────┘                        │
│              │                    │                                   │
│              ▼                    ▼                                   │
│  ┌───────────────────┐  ┌──────────────────────┐                    │
│  │ .cache/           │  │ vosk-model-small-     │                    │
│  │ sentence_trans-   │  │ hi-0.22/              │                    │
│  │ formers/          │  │ (Kaldi acoustic model)│                    │
│  │ (470 MB)          │  │ (50 MB)               │                    │
│  └───────────────────┘  └──────────────────────┘                    │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
                               │
                    PostgreSQL + pgvector
```

---

## 8. Tech Stack

| Layer             | Technology              | Version | Purpose                         |
| ----------------- | ----------------------- | ------- | ------------------------------- |
| Web Framework     | Django                  | 5.0.6   | HTTP routing, ORM, admin panel  |
| REST API          | Django REST Framework   | 3.15.2  | API views, serializers, parsers |
| API Docs          | drf-spectacular         | 0.27.2  | OpenAPI 3 schema + Swagger UI   |
| Production Server | Gunicorn                | 22.0.0  | WSGI server, 2 workers          |
| Database          | PostgreSQL              | 17      | Relational storage              |
| Vector Extension  | pgvector                | —       | Cosine similarity search        |
| DB Driver         | psycopg3                | 3.2.6   | PostgreSQL Python adapter       |
| pgvector Django   | pgvector                | 0.4.2   | VectorField ORM integration     |
| DB URL Parser     | dj-database-url         | 2.2.0   | Parse DATABASE_URL env var      |
| CORS              | django-cors-headers     | 4.4.0   | Cross-origin widget support     |
| Static Files      | WhiteNoise              | 6.7.0   | Serve static without nginx      |
| Environment       | python-dotenv           | 1.1.0   | Load .env file                  |
| Embeddings        | sentence-transformers   | 3.4.1   | Multilingual text embeddings    |
| Deep Learning     | PyTorch (CPU)           | 2.6.0   | Model inference backend         |
| Numerics          | NumPy                   | 1.26.4  | Vector operations               |
| Voice STT         | Vosk                    | 0.3.45  | Offline Hindi speech-to-text    |
| Deployment        | Render.com              | —       | Cloud hosting                   |
| Language          | Python                  | 3.12    | Runtime                         |
| Frontend Widget   | Vanilla JS + Shadow DOM | —       | Embeddable chatbot              |

---

## 9. ML Models

### 9.1 Embedding Model

| Property            | Value                                                          |
| ------------------- | -------------------------------------------------------------- |
| Model name          | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`  |
| Provider            | HuggingFace / sentence-transformers                            |
| Architecture        | MiniLM (12-layer transformer)                                  |
| Output dimensions   | 384 floats                                                     |
| Languages supported | 50+ (including Hindi, English)                                 |
| Model size on disk  | ~470 MB                                                        |
| Runtime device      | CPU                                                            |
| Cache location      | `.cache/sentence_transformers/` inside project root            |
| Input format        | `"{cropname} {problem}"` (crop prepended for better relevance) |
| Normalization       | L2-normalized embeddings (`normalize_embeddings=True`)         |
| Thread safety       | `_infer_lock` serializes `model.encode()` calls                |

**Why this model:** Supports Hindi natively, compact size (vs full multilingual models at 1.2GB+), and produces high-quality semantic similarity scores for agricultural terminology.

### 9.2 Voice Model

| Property           | Value                                             |
| ------------------ | ------------------------------------------------- |
| Model name         | `vosk-model-small-hi-0.22`                        |
| Provider           | Alpha Cephei (Vosk / Kaldi)                       |
| Architecture       | Kaldi acoustic model + HCLR FST graph             |
| Language           | Hindi (hi-IN)                                     |
| Model size on disk | ~50 MB                                            |
| Runtime device     | CPU                                               |
| Input format       | 16-bit mono WAV, 16kHz recommended                |
| Max file size      | 10 MB                                             |
| Thread safety      | Fresh `KaldiRecognizer` instance per request      |
| Offline            | Fully offline — no network calls during inference |

---

## 10. Search Algorithm

### Overview

The search pipeline in `services.py` combines vector similarity with keyword boosting to produce results that are both semantically relevant and symptom-specific.

```
Query
  │
  ├─── Step 1: Crop Detection ──────────────────────────────────────────
  │    detect_crop(query)
  │    4 strategies (in order):
  │      1. Full query exact match against CROP_ALIASES
  │      2. Exact token match (split on whitespace/punctuation)
  │      3. Prefix match (token ≥ 3 chars)
  │      4. Substring match
  │    Supports: Hindi forms, English names, inflections
  │    Examples: "टमाटरों" → "टमाटर", "tomatoes" → "टमाटर"
  │
  ├─── Step 2: Vector Search (pgvector) ───────────────────────────────
  │    generate_embedding(query)  →  384-dim float vector
  │
  │    SQL (with crop filter):
  │      SELECT id, problem, solution, cropname,
  │             (1 - (embedding <=> %s)) AS emb_score
  │      FROM solutions
  │      WHERE embedding IS NOT NULL
  │        AND cropname = %s
  │        AND (1 - (embedding <=> %s)) >= 0.2
  │      ORDER BY emb_score DESC
  │      LIMIT 50
  │
  │    Fetches 5× the final limit (50 candidates for top-10 output)
  │
  ├─── Step 3: Keyword Boost Re-ranking ───────────────────────────────
  │    For each candidate:
  │      For each of 21 symptom categories:
  │        if keyword in query AND keyword in candidate.problem:
  │          score += 0.30
  │      score = min(boost, 0.90)
  │
  │    final_score = embedding_score + boost
  │    (score can exceed 1.0 — intentional, keyword matches dominate)
  │
  │    21 symptom categories:
  │    fruit_drop, insect, hole, crack, black_spot, yellow, dry,
  │    rot, flower_drop, no_fruit, leaf_curl, white_fly, fungus,
  │    termite, growth, seed, irrigation, fertilizer, sour, sweet, taste
  │
  ├─── Step 4: Sort and Return ─────────────────────────────────────────
  │    sorted by final_score DESC
  │    return top-10
  │
  └─── Step 5: ILIKE Fallback ──────────────────────────────────────────
       Only if embedding model unavailable OR zero vector search results
       SELECT ... FROM solutions WHERE problem ILIKE '%query%'
       search_method = "fallback"
```

### Scoring Example

```
Query: "टमाटर में कीड़े लग गए हैं"
Detected crop: "टमाटर"

Candidate A (id=42, cropname="टमाटर"):
  embedding_score = 0.74
  keyword matches: insect (कीड़े in both query + problem)
  boost = 0.30
  final_score = 1.04  ✅ top result

Candidate B (id=89, cropname="टमाटर"):
  embedding_score = 0.81
  keyword matches: none (talks about fungus, not insects)
  boost = 0.00
  final_score = 0.81

→ Candidate A ranks first despite lower embedding score
  because the keyword match is more relevant.
```

---

## 11. API Endpoints

Base URL (local): `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs/`  
OpenAPI schema: `http://localhost:8000/schema/`

### GET `/`

Serves `chatbot.html` — the standalone chatbot UI.

### GET `/health`

```json
{
	"status": "healthy",
	"model_loaded": true,
	"database_connected": true,
	"voice_model_loaded": true
}
```

Status is `"degraded"` if embedding model or DB is unavailable.

### POST `/init-db`

Enables pgvector extension and creates the IVFFLAT similarity index.  
Run once after fresh deployment.

```json
{ "message": "pgvector extension enabled and index created." }
```

### POST `/generate-embeddings`

Backfills `NULL` embeddings for all records in the `solutions` table.

```json
{
	"message": "Generated embeddings for 1523 records",
	"processed": 1523,
	"failed": 0,
	"total": 1523
}
```

### GET `/all`

Returns all records. No filter, no pagination.

### GET `/search?q=<query>`

Returns top-10 results. Requires crop name in query.

```
GET /search?q=टमाटर में कीड़े लग गए हैं
```

```json
[
	{
		"id": 42,
		"cropname": "टमाटर",
		"problem": "टमाटर में माहू कीट लग गया है",
		"solution": "इमिडाक्लोप्रिड 0.5 ml/L पानी में घोलकर छिड़काव करें",
		"similarity_score": 1.04,
		"search_method": "semantic_crop",
		"detected_crop": "टमाटर"
	}
]
```

### POST `/search`

Body: `{"q": "टमाटर में कीड़े"}` — Returns top-1 result only (chatbot mode).

### POST `/voice`

Multipart form: `audio` = WAV file  
Returns Hindi transcript only.

```json
{ "transcript": "टमाटर में कीड़े लग गए हैं", "success": true }
```

### POST `/voice-search`

Multipart form: `audio` = WAV file  
One-shot: voice → transcript → crop solution.

```json
{
	"transcript": "टमाटर में कीड़े लग गए हैं",
	"result": { "id": 42, "cropname": "टमाटर", "solution": "..." }
}
```

### GET `/docs/`

Swagger UI — interactive API explorer with file upload support.

### GET `/schema/`

Raw OpenAPI 3 JSON schema.

### GET/POST `/admin/`

Django admin panel (requires superuser login).

---

## 12. Database Schema

```sql
-- Enable pgvector extension (run once)
CREATE EXTENSION IF NOT EXISTS vector;

-- Main solutions table (pre-existing, managed=False in Django)
CREATE TABLE solutions (
    id        SERIAL PRIMARY KEY,
    cropname  VARCHAR(500) NOT NULL,
    problem   TEXT NOT NULL,
    solution  TEXT NOT NULL,
    embedding VECTOR(384)           -- 384-dim cosine-normalized float array
);

-- Index for fast approximate nearest-neighbour search
CREATE INDEX solutions_embedding_idx
    ON solutions
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Index for cropname filtering
CREATE INDEX ON solutions (cropname);
```

**IVFFLAT index parameters:**

- `lists = 100` — 100 Voronoi cells; good for 1500–50000 rows
- `vector_cosine_ops` — cosine distance metric matches L2-normalized embeddings
- Query: `1 - (embedding <=> query_vector)` gives cosine similarity (0–1)

---

## 13. Embeddable Widget

### Integration

```html
<!-- Minimal -->
<script
	src="https://yourdomain.com/static/kisan-widget.js"
	data-api="https://yourdomain.com"
></script>

<!-- With position -->
<script
	src="https://yourdomain.com/static/kisan-widget.js"
	data-api="https://yourdomain.com"
	data-position="bottom-left"
></script>
```

### Widget Architecture

```
<script> tag loaded by host page
        │
        ▼
kisan-widget.js (IIFE)
        │
        ├── window.__kisanWidgetLoaded guard (double-init prevention)
        │
        ├── Read data-api, data-position from <script> tag
        │
        ├── document.createElement('div')  → #kisan-widget-host
        │   └── attachShadow({mode:'open'})
        │       ├── <style> (all CSS — scoped, isolated)
        │       └── HTML (toggle btn + widget panel)
        │
        ├── Event listeners (toggle, close, send, chips, voice)
        │
        └── Voice input:
            ├── Primary: window.SpeechRecognition (Chrome/Edge)
            └── Fallback: MediaRecorder → POST /voice → Vosk
```

### Configuration Attributes

| Attribute       | Default                       | Values                        |
| --------------- | ----------------------------- | ----------------------------- |
| `data-api`      | auto-detect from script `src` | Any base URL                  |
| `data-position` | `bottom-right`                | `bottom-right`, `bottom-left` |

### Shadow DOM Isolation

The widget uses Shadow DOM (`attachShadow`) which means:

- Host page CSS cannot style the widget
- Widget CSS cannot leak into host page
- No class name conflicts possible
- `z-index: 2147483647` (maximum) ensures it always appears on top

---

## 14. Admin Panel

URL: `http://localhost:8000/admin/`  
Requires: `python manage.py createsuperuser`

### Dashboard Stats (custom KisanAdminSite)

```
┌─────────────────────────────────────────────┐
│  🌾 Kisan AI Admin — Database Management    │
├─────────────────────────────────────────────┤
│  Total records:        1,523                │
│  With embeddings:      1,523  (100%)        │
│  Missing embeddings:   0                    │
├─────────────────────────────────────────────┤
│  Top 5 crops:                               │
│  1. टमाटर         (142 records)            │
│  2. आम             (98 records)            │
│  3. गेहूँ          (87 records)            │
│  4. आलू            (76 records)            │
│  5. बैंगन          (71 records)            │
└─────────────────────────────────────────────┘
```

### List View Columns

| Column           | Description                     |
| ---------------- | ------------------------------- |
| id               | Record ID                       |
| cropname         | Crop name (filterable)          |
| problem preview  | First 80 characters of problem  |
| solution preview | First 60 characters of solution |
| embedding status | ✅ Generated / ❌ Missing       |
| length           | Character count of problem text |

### Bulk Actions

| Action              | Description                                                          |
| ------------------- | -------------------------------------------------------------------- |
| Generate embeddings | Runs `embedding_generator.generate_embedding()` for selected records |
| Export to CSV       | Downloads UTF-8-BOM CSV (Excel-compatible) with all fields           |

### Auto-embedding Signal

When `problem` or `cropname` changes in the detail view and is saved:

1. Django `pre_save` signal fires on `Solution` model
2. `auto_generate_embedding()` compares old vs new `problem`
3. If changed → calls `embedding_generator.generate_embedding()`
4. New embedding stored before the save completes

---

## 15. Deployment Architecture

### Render.com (render.yaml)

```
┌─────────────────────────────────────────────────────────┐
│                    Render.com                            │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │           Web Service: kisan-ai-django             │  │
│  │                                                   │  │
│  │  Build:  pip install -r requirements.txt          │  │
│  │          python manage.py collectstatic --noinput │  │
│  │                                                   │  │
│  │  Start:  gunicorn kisan.wsgi:application          │  │
│  │          --bind 0.0.0.0:$PORT                     │  │
│  │          --workers 2                              │  │
│  │          --timeout 120                            │  │
│  │                                                   │  │
│  │  Env vars auto-set:                               │  │
│  │    DJANGO_SECRET_KEY  (generateValue: true)       │  │
│  │    DATABASE_URL       (from Render PostgreSQL)    │  │
│  │    DEBUG=False                                    │  │
│  └───────────────────────────────────────────────────┘  │
│                          │                               │
│                          │ DATABASE_URL                  │
│                          ▼                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │        Render PostgreSQL (kisan-db)                │  │
│  │        pgvector extension enabled                  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Static File Flow

```
Developer pushes code
        │
        ▼
Render build step:
  python manage.py collectstatic --noinput
        │
        ▼
All static files copied to /staticfiles/
        │
        ▼
WhiteNoise middleware serves from /staticfiles/
  GET /static/kisan-widget.js → 200 OK
```

### Cold Start Warning

On Render free tier, the first request after inactivity triggers a cold start. The embedding model (~470 MB) must load from disk — this takes ~15–30 seconds. The `--timeout 120` in gunicorn accommodates this.

---

## 16. Design Patterns

### Singleton + Double-Checked Locking

Both `EmbeddingGenerator` and `VoiceService` use the Singleton pattern with double-checked locking to ensure the ML model is loaded exactly once even under concurrent startup requests.

```python
class EmbeddingGenerator:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_model(self):
        if self._model is not None:       # fast path (no lock)
            return
        with self._load_lock:             # only one thread loads
            if self._model is not None:   # double-check after lock
                return
            self._model = SentenceTransformer(...)
```

### Thread-Safe Inference

```python
def generate_embedding(self, text):
    with self._infer_lock:                # serialise encode() calls
        vec = self._model.encode(text)
    return vec.tolist()
```

### Non-Blocking Semaphore (Voice Endpoints)

Voice endpoints use a non-blocking semaphore to immediately return 503 when at capacity rather than queuing requests:

```python
acquired = _voice_semaphore.acquire(blocking=False)
if not acquired:
    return Response({"detail": "Server busy"}, status=503)
try:
    ...  # transcribe
finally:
    _voice_semaphore.release()
```

### Shadow DOM (Widget Isolation)

```javascript
var host = document.createElement("div");
document.body.appendChild(host);
var shadow = host.attachShadow({ mode: "open" });
// All CSS and HTML injected into shadow — fully isolated
```

### Django Signal (Auto-Embedding)

```python
@receiver(pre_save, sender=Solution)
def auto_generate_embedding(sender, instance, **kwargs):
    if problem_changed:
        instance.embedding = embedding_generator.generate_embedding(
            f"{instance.cropname} {instance.problem}"
        )
```

### managed=False (Non-Destructive ORM)

```python
class Solution(models.Model):
    class Meta:
        db_table = "solutions"
        managed = False   # Django won't CREATE or DROP this table
```

---

## 17. Environment Variables

| Variable                          | Required | Default                         | Description                      |
| --------------------------------- | -------- | ------------------------------- | -------------------------------- |
| `DATABASE_URL`                    | ✅       | —                               | PostgreSQL connection string     |
| `DJANGO_SECRET_KEY`               | ✅       | insecure default                | Django secret key                |
| `DEBUG`                           | —        | `False`                         | `True` for local dev             |
| `ALLOWED_HOSTS`                   | —        | `*`                             | Comma-separated allowed hosts    |
| `DISABLE_EMBEDDINGS`              | —        | `false`                         | Skip embedding model entirely    |
| `SENTENCE_TRANSFORMERS_HOME`      | —        | `.cache/sentence_transformers/` | Model cache path                 |
| `HF_HOME`                         | —        | `.cache/huggingface/`           | HuggingFace cache root           |
| `CACHE_DIR`                       | —        | `.cache/sentence_transformers/` | Legacy cache override            |
| `VOSK_MODEL_PATH`                 | —        | auto-detect                     | Override Vosk model path         |
| `MAX_CONCURRENT_REQUESTS`         | —        | `10`                            | Max simultaneous voice requests  |
| `HF_HUB_DISABLE_SYMLINKS_WARNING` | —        | `1`                             | Suppress Windows symlink warning |

---

## 18. File Structure

```
KisanDjango/
│
├── manage.py                    Django CLI + HF env var setup
├── requirements.txt             All Python dependencies (pinned)
├── Procfile                     Render/Heroku process definition
├── render.yaml                  Render deployment config
├── .env                         Local secrets (not committed)
├── .env.example                 Template for .env
├── .gitignore                   Excludes .venv, .cache, vosk model
├── .gitattributes               LF line endings across platforms
├── chatbot.html                 Standalone chatbot UI
├── services.py                  Core search logic
├── embedding_service.py         Embedding singleton
├── voice_service.py             Vosk STT singleton
│
├── static/
│   └── kisan-widget.js          Embeddable widget (Shadow DOM IIFE)
│
├── kisan/                       Django project config
│   ├── settings.py              All settings + env loading
│   ├── urls.py                  Root URL routing
│   └── wsgi.py                  WSGI entry point
│
├── api/                         Django app
│   ├── __init__.py
│   ├── apps.py                  AppConfig + ML model preload
│   ├── models.py                Solution model (managed=False)
│   ├── serializers.py           DRF serializers
│   ├── views.py                 All 9 API endpoint views
│   ├── urls.py                  App-level URL routing
│   ├── admin.py                 Custom admin site + bulk actions
│   └── exceptions.py            Custom DRF exception handler
│
├── templates/
│   └── admin/
│       └── index.html           Custom admin dashboard template
│
├── .cache/                      Downloaded models (not committed)
│   ├── huggingface/
│   └── sentence_transformers/   paraphrase-multilingual-MiniLM (~470 MB)
│
└── vosk-model-small-hi-0.22/   Vosk Hindi model (~50 MB, not committed)
    ├── am/final.mdl
    ├── conf/
    ├── graph/
    └── ivector/
```

---

## 19. Known Issues & Fixes

| Issue                                              | Root Cause                                                                  | Fix Applied                                                                                                                    |
| -------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `NameError: CropQuestions` on startup              | Stale SQLAlchemy type annotation after Django migration                     | Renamed to `CropResult` throughout `services.py`                                                                               |
| Embedding model `FileNotFoundError` on Windows     | HuggingFace uses symlinks; Windows blocks them without Developer Mode       | Set `HF_HOME` + `SENTENCE_TRANSFORMERS_HOME` in `manage.py` before any imports; load from existing snapshot directory directly |
| `model_loaded: false` in health check              | `RUN_MAIN` guard inverted — models loaded in watcher process, not worker    | Fixed: load when `RUN_MAIN=true` (the worker process that handles requests)                                                    |
| `GET /static/kisan-widget.js` → 404                | `DEBUG=False` disables Django's built-in static file serving                | Added `static()` route in `urls.py`; added `STATICFILES_DIRS` to settings                                                      |
| Server crash: `ModuleNotFoundError: pkg_resources` | Abandoned `rest_framework_swagger` package incompatible with Python 3.12    | Removed; replaced with `drf-spectacular 0.27.2`                                                                                |
| Swagger shows "No parameters" for POST /search     | drf-spectacular can't auto-detect `request.data.get()` without a serializer | Added `@extend_schema` with `SearchPostSerializer`                                                                             |
| Swagger shows `string($uri)` for voice file upload | `FileField` serializer renders as URI in OpenAPI                            | Replaced with raw OpenAPI binary schema dict in `@extend_schema`                                                               |
| Cache path mismatch (`~/.cache` despite env vars)  | `SENTENCE_TRANSFORMERS_HOME` set after library import                       | Moved env var setup to top of `manage.py` before all imports                                                                   |

---

_Generated: June 2026 | Kisan AI Django API v1.0.0_

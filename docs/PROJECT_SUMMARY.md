# KisanDjango - Agricultural Advisory System

## Project Overview
KisanDjango is a **Django-based agricultural advisory chatbot** that helps farmers identify crop problems and find solutions. It supports **Hindi and English** queries and uses **semantic search with AI embeddings** to match user queries with relevant agricultural solutions.

---

## Core Functionality
The system takes a farmer's problem description (e.g., "टमाटर में कीड़े लग गए हैं" / "tomato has insects") and returns the best matching solution from a database of agricultural knowledge.

---

## Architecture

### Tech Stack
- **Backend**: Django 5.0.6 + Django REST Framework
- **Database**: PostgreSQL with pgvector extension (768-dimensional vectors)
- **ML Model**: nomic-ai/nomic-embed-text-v1.5 (sentence-transformers)
- **Voice**: Vosk Hindi STT model (vosk-model-small-hi-0.22)
- **API Docs**: drf-spectacular (OpenAPI/Swagger)

### Key Components

#### 1. **services.py** - Core Search Logic
The heart of the system. Implements hybrid search algorithm:

**Flow:**
```
User Query → Crop Detection → Intent Classification → Hybrid Search → Results
```

**Key Functions:**

- **`detect_crop(query)`**: Extracts crop name from query using pattern matching
  - Supports 200+ Hindi/English crop name variations
  - Uses exact match, prefix match, and substring matching
  - Example: "टमाटर", "tomato", "टमाटरों" all map to "टमाटर"

- **`classify_query(query)`**: Determines if query is a problem or general question
  - Returns "problem" or "general"
  - Filters out how-to farming questions without specific problems

- **`search_crop_solution(db, query)`**: Main search entry point
  - Calls semantic search with hybrid scoring
  - Falls back to ILIKE search on exceptions
  - Returns empty list if no match (triggers support message)

- **`search_crop_solution_semantic()`**: Hybrid retrieval algorithm
  ```
  Step 1: Vector search (pgvector) - get top 50 candidates with cosine similarity > 0.15
  Step 2: Keyword boost scoring - add 0.3 for each matching symptom category
  Step 3: Primary symptom boost - add +1.5 for exact symptom match, -1.5 for mismatch
  Step 4: Word overlap filter - remove irrelevant results
  Step 5: Return top 10, filtered by MIN_RETURN_SCORE (0.45)
  ```

- **`hybrid_score(emb_score, query, problem)`**: Calculates final ranking score
  ```python
  final_score = embedding_similarity + keyword_boost + primary_symptom_boost
  ```

- **`normalize_text(text)`**: Normalizes Hindi text for better matching
  - Converts inflections to root forms: "सड़ रहे हैं" → "सड़"
  - Removes postpositions: "में", "पर", "से", etc.
  - Handles continuous tense markers

- **`keyword_boost(query, problem)`**: Adds score for symptom keyword matches
  - 18 symptom categories (rot, yellow, dry, insect, etc.)
  - +0.3 per matching category, max +0.9

**Important Data Structures:**

- **`CROP_ALIASES`**: 200+ crop name mappings (Hindi ↔ English)
- **`SYMPTOM_KEYWORDS`**: 18 symptom categories with Hindi/English keywords
- **`QUERY_NORMALIZATION`**: 60+ Hindi text normalization rules
- **`PRIMARY_SYMPTOMS`**: 5 main symptom types for exact matching (rot, yellow, dry, black_spot, insect)
- **`MIN_RETURN_SCORE`**: 0.45 (minimum score threshold)
- **`NO_ANSWER_MESSAGE`**: Support message when no solution found

---

#### 2. **embedding_service.py** - AI Embeddings
Manages the sentence transformer model for semantic search.

**Key Class: `EmbeddingGenerator`**
- Loads nomic-ai/nomic-embed-text-v1.5 model (768 dimensions)
- Generates embeddings for text queries
- Caches model in `.cache/sentence_transformers/`
- Thread-safe with locks
- Prefix handling: adds "search_query: " or "search_document: " for optimal results

**Methods:**
- `load_model()`: Initializes the transformer model
- `generate_embedding(text)`: Creates 768-dim vector from text
- `is_model_loaded()`: Checks if model is ready

---

#### 3. **api/views.py** - REST API Endpoints
Django REST Framework views implementing the API.

**Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Serve chatbot HTML UI |
| GET | `/health` | Health check (model + DB status) |
| POST | `/init-db` | Initialize pgvector extension & index |
| POST | `/generate-embeddings` | Backfill missing embeddings |
| GET | `/all` | Get all crop solutions (paginated) |
| GET | `/search?q=...` | Search (returns top 10) |
| POST | `/search` | Search (returns top 3 for chatbot) |
| POST | `/voice` | Transcribe Hindi audio to text |
| POST | `/voice-search` | Audio → transcript → solution (one-shot) |

**Key Features:**
- **SearchView**: Main search endpoint with intent classification
  - Returns top 3 results for POST (chatbot mode)
  - Returns top 10 results for GET (general search)
  - Handles "general query" and "no crop detected" cases
  
- **VoiceView**: Audio transcription only
  - Max 10 MB WAV files
  - Concurrency limited by semaphore (10 concurrent max)
  
- **VoiceSearchView**: Combined audio + search
  - Transcribes → detects crop → searches → returns results

---

#### 4. **api/models.py** - Database Schema
Django ORM models for PostgreSQL.

**Main Model: `Solution`**
```python
class Solution(models.Model):
    id = AutoField(primary_key=True)
    cropname = CharField(max_length=200)      # Crop name (Hindi)
    problem = TextField()                     # Problem description
    solution = TextField()                    # Solution/remedy
    embedding = VectorField(dimensions=768)   # AI embedding vector
```

**Database:**
- Table: `solutions`
- Index: `solutions_embedding_idx` (IVFFLAT for vector search)
- Extension: pgvector

---

#### 5. **voice_service.py** - Speech Recognition
Handles Hindi speech-to-text using Vosk.

**Key Class: `VoiceService`**
- Loads Vosk Hindi model (vosk-model-small-hi-0.22)
- Converts WAV audio (16kHz mono) to Hindi text
- Thread-safe with locks

**Methods:**
- `load_model()`: Initialize Vosk recognizer
- `transcribe(audio_bytes)`: WAV → Hindi text
- `is_model_loaded()`: Check if ready

---

#### 6. **kisan/settings.py** - Django Configuration
Main Django settings including:
- Database: PostgreSQL connection
- Installed apps: DRF, drf-spectacular, corsheaders
- Vector field support
- CORS settings for frontend
- Logging configuration
- Static files setup

---

## Search Algorithm Deep Dive

### Hybrid Scoring Formula
```
final_score = embedding_score + keyword_boost + primary_symptom_boost
```

**Components:**

1. **Embedding Score** (0-1): Cosine similarity from vector search
2. **Keyword Boost** (0-0.9): +0.3 per matching symptom category
3. **Primary Symptom Boost** (-1.5 to +1.5):
   - **+1.5**: Query symptom matches problem symptom exactly
   - **-1.5**: Query symptom doesn't match problem symptom
   - **-0.8**: Query has symptom, problem has none

### Example Scoring

**Query:** "अरवी के पत्ते में सड़न हो रही है" (rot in taro leaves)

**Candidate 1:** "अरवी के पत्ते सड़ रहे हैं" (taro leaves rotting)
- Embedding: 0.92
- Keyword boost: +0.3 (rot keyword match)
- Primary symptom: +1.5 (both have rot)
- **Final: 2.72** ✓ TOP MATCH

**Candidate 2:** "अरवी के पत्ते पीले हो रहे हैं" (taro leaves yellowing)
- Embedding: 0.92
- Keyword boost: 0.0 (no keyword match)
- Primary symptom: -1.5 (rot vs yellow mismatch)
- **Final: -0.58** ✗ REJECTED

---

## Text Normalization System

### Purpose
Handles Hindi language inflections for better matching.

### Examples
```
"सड़ रहे हैं" → "सड़"  (rotting → rot)
"पीले हो रहे" → "पीला" (yellowing → yellow)
"गलन" → "सड़"          (decay → rot)
"धब्बे" → "धब्बा"      (spots → spot)
```

### Process
1. Convert to lowercase
2. Sort replacements by length (longest first)
3. Apply 60+ normalization rules
4. Remove postpositions and verb helpers
5. Collapse multiple spaces

---

## Key Files & Their Roles

```
KisanDjango/
├── api/
│   ├── models.py          # Database schema (Solution model)
│   ├── views.py           # REST API endpoints
│   ├── serializers.py     # DRF serializers
│   ├── urls.py            # API route definitions
│   └── admin.py           # Django admin customization
│
├── kisan/
│   ├── settings.py        # Django configuration
│   ├── urls.py            # Main URL routing
│   └── wsgi.py            # WSGI application
│
├── services.py            # CORE: Search logic & hybrid algorithm
├── embedding_service.py   # AI embedding generation
├── voice_service.py       # Speech-to-text (Vosk)
│
├── manage.py              # Django management commands
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (DB, secrets)
├── Procfile               # Deployment config (Render/Heroku)
│
├── static/
│   └── kisan-widget.js    # Frontend chatbot widget
│
├── templates/
│   └── admin/index.html   # Custom admin dashboard
│
├── chatbot.html           # Standalone chatbot UI
│
└── Tests:
    ├── test_api_call.py       # API endpoint testing
    ├── test_accuracy.py       # Search accuracy evaluation
    ├── test_direct_search.py  # Direct services.py testing
    └── adv_data_test.csv      # Test dataset
```

---

## Database Schema

### Table: `solutions`
```sql
CREATE TABLE solutions (
    id SERIAL PRIMARY KEY,
    cropname VARCHAR(200),
    problem TEXT,
    solution TEXT,
    embedding vector(768)  -- pgvector type
);

-- Vector similarity index (IVFFLAT)
CREATE INDEX solutions_embedding_idx 
ON solutions 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

---

## API Request/Response Examples

### POST /search
**Request:**
```json
{
  "q": "टमाटर के पत्ते पीले हो रहे हैं"
}
```

**Response:**
```json
[
  {
    "id": 45,
    "cropname": "टमाटर",
    "problem": "टमाटर के पत्ते पीले हो रहे हैं क्या करें?",
    "solution": "यह नाइट्रोजन की कमी हो सकती है...",
    "similarity_score": 2.45,
    "search_method": "semantic_crop",
    "detected_crop": "टमाटर"
  },
  {
    "id": 78,
    "cropname": "टमाटर",
    "problem": "टमाटर पीले पड़ रहे हैं",
    "solution": "पौधों में यूरिया का छिड़काव करें...",
    "similarity_score": 2.12,
    "search_method": "semantic_crop",
    "detected_crop": "टमाटर"
  }
]
```

---

## Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Model Cache (optional)
TRANSFORMERS_CACHE=.cache/sentence_transformers/
```

---

## Deployment

### Requirements
- Python 3.10+
- PostgreSQL 14+ with pgvector extension
- 4GB+ RAM (for embedding model)
- ~2GB disk (for models)

### Setup Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Database migrations
python manage.py migrate

# Initialize pgvector
curl -X POST http://localhost:8000/init-db

# Generate embeddings
curl -X POST http://localhost:8000/generate-embeddings

# Run server
python manage.py runserver
```

---

## Testing

### Test Files
- **test_api_call.py**: Tests POST /search endpoint
- **test_accuracy.py**: Evaluates search accuracy on test dataset
- **test_direct_search.py**: Tests services.py functions directly
- **test_quick.py**: Quick sanity checks

### Run Tests
```bash
python test_api_call.py
python test_accuracy.py
```

---

## Recent Improvements Applied

### Query Normalization Enhancement
- Added comprehensive Hindi text normalization (60+ rules)
- Normalizes inflections: "सड़ रहे हैं" → "सड़"
- Removes postpositions and verb helpers

### Primary Symptom Matching
- Exact symptom matching with +1.5/-1.5 scoring
- 5 main symptom types: rot, yellow, dry, black_spot, insect
- Overrides generic keyword matching for precision

### API Response Changes
- POST /search now returns top 3 results (was top 1)
- Better for chatbot to show multiple options

### Score Threshold
- Lowered MIN_RETURN_SCORE from 0.55 to 0.45
- Returns more results while maintaining quality

---

## Common Issues & Solutions

### Issue: Model Not Loading
**Solution:** Check `.cache/` folder exists and has write permissions

### Issue: No Results Returned
**Causes:**
1. Crop not detected → Add crop alias to CROP_ALIASES
2. Low similarity scores → Check MIN_RETURN_SCORE threshold
3. No embeddings → Run /generate-embeddings

### Issue: Wrong Results
**Debug:**
1. Check crop detection: `services.detect_crop(query)`
2. Check normalization: `services.normalize_text(query)`
3. Review hybrid scores in logs
4. Add symptom keywords to SYMPTOM_KEYWORDS

---

## Key Design Decisions

### Why Hybrid Search?
Pure semantic search misses exact keyword matches. Pure keyword search misses semantic similarity. Hybrid combines both.

### Why Normalize Text?
Hindi has many inflections for the same root word. Normalization ensures "सड़ रहे हैं" and "सड़न" both map to "सड़" for matching.

### Why Primary Symptom Boost?
Prevents false positives from generic matches. "Rot" and "yellow leaves" are both common in crop problems, but are different issues requiring different treatments.

### Why Top 3 Results?
Gives users options when uncertainty exists, improving user experience over single-result forcing.

---

## Performance Characteristics

- **Search Latency**: 200-300ms average
  - 100-150ms: Embedding generation
  - 50-100ms: Vector search
  - 50ms: Re-ranking & filtering

- **Concurrency**: 
  - Voice endpoints: Max 10 concurrent (semaphore-limited)
  - Search endpoints: Limited by DB connections

- **Memory Usage**:
  - Embedding model: ~1.5GB RAM
  - Vosk model: ~300MB RAM
  - Base Django: ~100MB RAM

---

## Future Enhancement Ideas

1. **Multi-language Support**: Add more regional languages
2. **Image Recognition**: Upload crop photos for visual diagnosis
3. **Weather Integration**: Factor in local weather conditions
4. **User Feedback Loop**: Learn from user selections
5. **Caching Layer**: Redis for frequent queries
6. **A/B Testing**: Compare different scoring algorithms
7. **Analytics Dashboard**: Track query patterns and success rates

---

## Key Contacts & Resources

- **Model**: [nomic-ai/nomic-embed-text-v1.5](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5)
- **Voice Model**: [Vosk Hindi Model](https://alphacephei.com/vosk/models)
- **pgvector**: [GitHub](https://github.com/pgvector/pgvector)
- **Django**: [Documentation](https://docs.djangoproject.com/)

---

## Summary for AI Editors

**This is a bilingual agricultural chatbot that helps farmers solve crop problems using AI-powered semantic search.**

**Core flow:** Query → Detect Crop → Normalize Text → Vector Search → Keyword Boost → Primary Symptom Matching → Return Top 3 Solutions

**Most important file:** `services.py` contains all search logic

**Key algorithm:** Hybrid scoring = embedding similarity + keyword boost + symptom boost

**Languages:** Hindi + English, with extensive Hindi text normalization

**Database:** PostgreSQL with pgvector for 768-dimensional embeddings

**Current focus:** Improving search accuracy through better symptom detection and text normalization

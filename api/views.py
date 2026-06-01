"""
api/views.py

Django REST Framework views — port of every FastAPI endpoint in main.py.

Endpoint mapping:
  GET  /                  → ChatbotView       (serve chatbot.html)
  GET  /health            → HealthView
  POST /init-db           → InitDbView
  POST /generate-embeddings → GenerateEmbeddingsView
  GET  /all               → AllCropsView
  GET  /search?q=...      → SearchView (GET)
  POST /search            → SearchView (POST, body: {"q": "..."})
  POST /voice             → VoiceView
  POST /voice-search      → VoiceSearchView

Concurrency:
  Voice endpoints share a threading.Semaphore (MAX_CONCURRENT_VOICE from settings).
  The semaphore is initialised once at import time from the Django settings value.
"""

import logging
import os
import threading
import time

from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.db import connection, OperationalError, DatabaseError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

import services
from embedding_service import embedding_generator
from voice_service import voice_service

logger = logging.getLogger(__name__)

# ── Voice concurrency limiter ─────────────────────────────────────────────────
_MAX_VOICE = getattr(settings, "MAX_CONCURRENT_VOICE", 10)
_voice_semaphore = threading.Semaphore(_MAX_VOICE)


# ── Helper ────────────────────────────────────────────────────────────────────

def _result_to_dict(item, detected_crop=None):
    """Convert a CropResult (or Solution) object to a plain dict."""
    return {
        "id": item.id,
        "problem": item.problem,
        "solution": item.solution,
        "cropname": item.cropname,
        "similarity_score": getattr(item, "similarity_score", None),
        "search_method": getattr(item, "search_method", None),
        "detected_crop": detected_crop or getattr(item, "detected_crop", None),
    }


# ── Views ─────────────────────────────────────────────────────────────────────

class ChatbotView(APIView):
    """GET / — serve the chatbot HTML UI."""

    def get(self, request):
        html_path = os.path.join(settings.BASE_DIR, "chatbot.html")
        return FileResponse(open(html_path, "rb"), content_type="text/html")


class HealthView(APIView):
    """GET /health — liveness + readiness check."""

    def get(self, request):
        model_loaded = embedding_generator.is_model_loaded()
        voice_loaded = voice_service.is_model_loaded()

        database_connected = False
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            database_connected = True
        except Exception as exc:
            logger.error("DB health check failed: %s", exc, exc_info=True)

        status = "healthy" if model_loaded and database_connected else "degraded"
        if not model_loaded or not database_connected:
            logger.warning(
                "System degraded — model_loaded: %s, db: %s",
                model_loaded,
                database_connected,
            )

        return Response(
            {
                "status": status,
                "model_loaded": model_loaded,
                "database_connected": database_connected,
                "voice_model_loaded": voice_loaded,
            }
        )


class InitDbView(APIView):
    """
    POST /init-db — enable pgvector extension and create vector index.

    Note: Django migrations handle table creation.  This endpoint only
    ensures the pgvector extension and the IVFFLAT similarity index exist.
    """

    def post(self, request):
        try:
            with connection.cursor() as cursor:
                # Enable pgvector extension
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")

                # Create IVFFLAT index if absent
                cursor.execute(
                    "SELECT 1 FROM pg_indexes WHERE indexname = 'solutions_embedding_idx'"
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "CREATE INDEX solutions_embedding_idx "
                        "ON solutions USING ivfflat (embedding vector_cosine_ops) "
                        "WITH (lists = 100)"
                    )
            return Response({"message": "pgvector extension enabled and index created."})
        except Exception as exc:
            logger.error("init-db error: %s", exc, exc_info=True)
            return Response({"message": str(exc)}, status=500)


class GenerateEmbeddingsView(APIView):
    """POST /generate-embeddings — backfill missing embeddings."""

    def post(self, request):
        if not embedding_generator.is_model_loaded():
            logger.info("Embedding model not loaded, loading now...")
            embedding_generator.load_model()

        if not embedding_generator.is_model_loaded():
            return Response(
                {"message": "Embedding model failed to load. Check logs for details."},
                status=503,
            )

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, cropname, problem FROM solutions WHERE embedding IS NULL"
                )
                records = cursor.fetchall()

            if not records:
                return Response(
                    {"message": "All records already have embeddings", "processed": 0, "total": 0}
                )

            logger.info("Found %d records without embeddings", len(records))
            processed = failed = 0

            for record_id, cropname, problem in records:
                try:
                    text_for_embedding = f"{cropname} {problem}"
                    emb = embedding_generator.generate_embedding(text_for_embedding)
                    if emb:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "UPDATE solutions SET embedding = %s WHERE id = %s",
                                [str(emb), record_id],
                            )
                        processed += 1
                        logger.info("Embedded record id=%s", record_id)
                    else:
                        failed += 1
                        logger.warning("Embedding returned None for id=%s", record_id)
                except Exception as exc:
                    failed += 1
                    logger.error("Error embedding id=%s: %s", record_id, exc)

            return Response(
                {
                    "message": f"Generated embeddings for {processed} records",
                    "processed": processed,
                    "failed": failed,
                    "total": len(records),
                }
            )

        except Exception as exc:
            logger.error("generate-embeddings error: %s", exc, exc_info=True)
            return Response({"message": str(exc)}, status=500)


class AllCropsView(APIView):
    """GET /all — return every record (paginated by DB, no filter)."""

    def get(self, request):
        results = services.get_all_crops()
        return Response([_result_to_dict(r) for r in results])


class SearchView(APIView):
    """
    GET  /search?q=<query>   → returns top-10 results
    POST /search  {"q": ...} → returns top-1 result (chatbot mode)
    """

    def _run_search(self, query: str):
        """Shared search logic; returns (results_list_or_none, error_response_or_none)."""
        detected_crop = services.detect_crop(query)
        if not detected_crop:
            return None, Response(
                {
                    "message": "फसल का नाम स्पष्ट नहीं है। कृपया अपने प्रश्न में फसल का नाम लिखें।",
                    "hint": "उदाहरण: 'टमाटर में कीड़े लग गए हैं' या 'wheat disease treatment'",
                    "query": query,
                },
                status=400,
            )
        return detected_crop, None

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"error": "Query parameter 'q' is required."}, status=400)

        start = time.time()
        try:
            detected_crop, err = self._run_search(query)
            if err:
                return err

            results = services.search_crop_solution(None, query)
            elapsed = time.time() - start

            for item in results:
                item.detected_crop = detected_crop

            logger.info(
                "Search GET — query='%s', crop='%s', results=%d, time=%.3fs",
                query, detected_crop, len(results), elapsed,
            )

            if results:
                return Response([_result_to_dict(r, detected_crop) for r in results])

            return Response(
                {"message": "कोई समाधान नहीं मिला", "query": query, "detected_crop": detected_crop},
                status=404,
            )

        except (OperationalError, DatabaseError) as exc:
            logger.error("DB error in GET /search: %s", exc, exc_info=True)
            return Response(
                {"message": "Database temporarily unavailable", "error": "service_unavailable"},
                status=503,
            )
        except Exception as exc:
            logger.error("GET /search error: %s", exc, exc_info=True)
            return Response(
                {"message": "Internal server error", "error": str(exc), "query": query},
                status=500,
            )

    def post(self, request):
        query = (request.data.get("q") or "").strip()
        if not query:
            return Response({"error": "Field 'q' is required."}, status=400)

        start = time.time()
        try:
            detected_crop, err = self._run_search(query)
            if err:
                return err

            results = services.search_crop_solution(None, query)
            elapsed = time.time() - start

            for item in results:
                item.detected_crop = detected_crop

            logger.info(
                "Search POST — query='%s', crop='%s', results=%d, time=%.3fs",
                query, detected_crop, len(results), elapsed,
            )

            if results:
                return Response(_result_to_dict(results[0], detected_crop))

            return Response(
                {"message": "कोई समाधान नहीं मिला", "query": query, "detected_crop": detected_crop},
                status=404,
            )

        except (OperationalError, DatabaseError) as exc:
            logger.error("DB error in POST /search: %s", exc, exc_info=True)
            return Response(
                {"message": "Database temporarily unavailable", "error": "service_unavailable"},
                status=503,
            )
        except Exception as exc:
            logger.error("POST /search error: %s", exc, exc_info=True)
            return Response(
                {"message": "Internal server error", "error": str(exc), "query": query},
                status=500,
            )


class VoiceView(APIView):
    """
    POST /voice — WAV file → Hindi transcript only.

    Limited by _voice_semaphore to MAX_CONCURRENT_VOICE simultaneous calls.
    Returns 503 immediately if the semaphore is exhausted.
    """

    parser_classes = [MultiPartParser]

    ALLOWED_CONTENT_TYPES = {"audio/wav", "audio/wave", "audio/x-wav", "application/octet-stream"}
    MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB

    def post(self, request):
        audio_file = request.FILES.get("audio")
        if not audio_file:
            return Response({"detail": "No audio file provided. Send a WAV file as 'audio'."}, status=400)

        if audio_file.content_type not in self.ALLOWED_CONTENT_TYPES:
            return Response(
                {"detail": "Unsupported file type. Please upload a WAV audio file."},
                status=415,
            )

        if not voice_service.is_model_loaded():
            if not voice_service.load_model():
                return Response(
                    {"detail": "Voice model not available. Place 'vosk-model-small-hi-0.22' in the project root."},
                    status=503,
                )

        # Non-blocking semaphore check — reject immediately if at capacity
        acquired = _voice_semaphore.acquire(blocking=False)
        if not acquired:
            return Response(
                {"detail": f"Server busy. Max {_MAX_VOICE} concurrent voice requests. Please retry."},
                status=503,
            )

        try:
            audio_bytes = audio_file.read()

            if not audio_bytes:
                return Response({"detail": "Empty audio file received."}, status=400)
            if len(audio_bytes) > self.MAX_AUDIO_BYTES:
                return Response({"detail": "Audio file too large. Maximum size is 10 MB."}, status=413)

            transcript = voice_service.transcribe(audio_bytes)

            if not transcript:
                return Response(
                    {
                        "transcript": "",
                        "success": False,
                        "message": "कोई आवाज़ नहीं पहचानी गई। कृपया स्पष्ट रूप से बोलें।",
                    },
                    status=422,
                )

            logger.info("Voice transcript: '%s'", transcript)
            return Response({"transcript": transcript, "success": True})

        except Exception as exc:
            logger.error("Voice transcription error: %s", exc, exc_info=True)
            return Response({"detail": f"Transcription failed: {exc}"}, status=500)
        finally:
            _voice_semaphore.release()


class VoiceSearchView(APIView):
    """
    POST /voice-search — WAV file → transcript → crop solution (one-shot).

    Combines VoiceView + SearchView in a single request.
    Same concurrency limit as VoiceView.
    """

    parser_classes = [MultiPartParser]

    ALLOWED_CONTENT_TYPES = {"audio/wav", "audio/wave", "audio/x-wav", "application/octet-stream"}
    MAX_AUDIO_BYTES = 10 * 1024 * 1024

    def post(self, request):
        start = time.time()

        audio_file = request.FILES.get("audio")
        if not audio_file:
            return Response({"detail": "No audio file provided."}, status=400)

        if audio_file.content_type not in self.ALLOWED_CONTENT_TYPES:
            return Response({"detail": "Unsupported file type. Please upload a WAV audio file."}, status=415)

        if not voice_service.is_model_loaded():
            if not voice_service.load_model():
                return Response({"detail": "Voice model not available."}, status=503)

        acquired = _voice_semaphore.acquire(blocking=False)
        if not acquired:
            return Response(
                {"detail": f"Server busy. Max {_MAX_VOICE} concurrent voice requests. Please retry."},
                status=503,
            )

        try:
            audio_bytes = audio_file.read()

            if not audio_bytes:
                return Response({"detail": "Empty audio file received."}, status=400)
            if len(audio_bytes) > self.MAX_AUDIO_BYTES:
                return Response({"detail": "Audio file too large. Maximum 10 MB."}, status=413)

            transcript = voice_service.transcribe(audio_bytes)

            if not transcript:
                return Response(
                    {
                        "transcript": "",
                        "success": False,
                        "message": "कोई आवाज़ नहीं पहचानी गई। कृपया स्पष्ट रूप से बोलें।",
                    },
                    status=422,
                )

            logger.info("Voice-search transcript: '%s'", transcript)

            detected_crop = services.detect_crop(transcript)
            if not detected_crop:
                return Response(
                    {
                        "transcript": transcript,
                        "message": "फसल का नाम स्पष्ट नहीं है। कृपया फसल का नाम बोलें।",
                        "hint": "उदाहरण: 'टमाटर में कीड़े लग गए हैं'",
                    },
                    status=400,
                )

            results = services.search_crop_solution(None, transcript)
            elapsed = time.time() - start

            for item in results:
                item.detected_crop = detected_crop

            logger.info(
                "Voice-search — transcript='%s', crop='%s', results=%d, time=%.3fs",
                transcript, detected_crop, len(results), elapsed,
            )

            if results:
                return Response(
                    {"transcript": transcript, "result": _result_to_dict(results[0], detected_crop)}
                )

            return Response(
                {"transcript": transcript, "result": None, "message": "कोई समाधान नहीं मिला"},
                status=404,
            )

        except (OperationalError, DatabaseError) as exc:
            logger.error("DB error in voice-search: %s", exc, exc_info=True)
            return Response(
                {"transcript": locals().get("transcript", ""), "message": "Database temporarily unavailable"},
                status=503,
            )
        except Exception as exc:
            logger.error("Voice-search error: %s", exc, exc_info=True)
            return Response({"detail": str(exc)}, status=500)
        finally:
            _voice_semaphore.release()

"""
api/apps.py

AppConfig for the Kisan AI api app.
Handles ML model loading on Django startup — equivalent to FastAPI's @on_event("startup").

Double-load prevention:
  Django's dev server launches TWO processes (one for auto-reload detection).
  We only load models in the main worker process, identified by the absence of
  the RUN_MAIN env var (which the reloader child sets to 'true').
  Under gunicorn (production) RUN_MAIN is never set, so models load normally.
"""

import os
import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        """Called once when Django is fully initialised."""

        # Django's dev-server reloader calls ready() in BOTH the outer watcher
        # process and the inner worker process (RUN_MAIN='true').
        # We load models in the WORKER process (RUN_MAIN='true') because that
        # is the process that actually handles HTTP requests.
        # In production (gunicorn) RUN_MAIN is never set — models load once.
        if os.environ.get("RUN_MAIN") != "true" and os.environ.get("RUN_MAIN") is not None:
            # This is the outer reloader watcher — skip loading here.
            logger.info("Skipping model pre-load in reloader watcher process.")
            return

        logger.info("Django ready — pre-loading ML models...")

        try:
            from embedding_service import embedding_generator
            embedding_generator.load_model()
            if embedding_generator.is_model_loaded():
                logger.info("✅  Embedding model loaded.")
            else:
                logger.warning("⚠️  Embedding model failed to load (degraded mode).")
        except Exception as exc:
            logger.error("Embedding model load error: %s", exc, exc_info=True)

        try:
            from voice_service import voice_service
            voice_service.load_model()
            if voice_service.is_model_loaded():
                logger.info("✅  Vosk Hindi STT model loaded.")
            else:
                logger.warning("⚠️  Vosk model not found — voice endpoints will be unavailable.")
        except Exception as exc:
            logger.error("Voice model load error: %s", exc, exc_info=True)

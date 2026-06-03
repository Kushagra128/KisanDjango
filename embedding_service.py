import os
import time
import logging
import threading
from typing import List, Optional

# HF_HOME / SENTENCE_TRANSFORMERS_HOME must already be set by manage.py / wsgi.py
# before this module is imported. We just suppress the symlink warning here as a
# belt-and-suspenders measure.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _resolve_cache_dir() -> str:
    """
    Return the cache directory for sentence-transformers models.

    Priority:
      1. SENTENCE_TRANSFORMERS_HOME env var  (set by manage.py / wsgi.py)
      2. CACHE_DIR env var  (legacy / deployment override)
      3. .cache/sentence_transformers inside the project root
    """
    if os.environ.get("SENTENCE_TRANSFORMERS_HOME"):
        return os.environ["SENTENCE_TRANSFORMERS_HOME"]
    if os.environ.get("CACHE_DIR"):
        return os.environ["CACHE_DIR"]
    project_root = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(project_root, ".cache", "sentence_transformers")


class EmbeddingGenerator:
    """
    Thread-safe singleton for generating text embeddings.

    Concurrency design:
    - _load_lock  : ensures only ONE thread loads the model (others wait)
    - _infer_lock : serialises model.encode() calls so concurrent requests
                    don't corrupt each other's numpy buffers
    - Singleton   : one model instance shared across all requests (~420 MB)
    """

    _instance: Optional["EmbeddingGenerator"] = None

    MODEL_NAME        = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIM     = 384
    MAX_TEXT_CHARS    = 10_000
    WARN_LATENCY_MS   = 300

    DISABLE = os.getenv("DISABLE_EMBEDDINGS", "false").lower() == "true"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialised"):
            return
        self._initialised  = True
        self._model: Optional[SentenceTransformer] = None
        self._load_lock  = threading.Lock()
        self._infer_lock = threading.Lock()

    # ── Model loading ─────────────────────────────────────────────────────────

    def load_model(self) -> None:
        """Load the model exactly once, even under concurrent startup calls."""
        if self.DISABLE:
            logger.warning("Embeddings disabled (DISABLE_EMBEDDINGS=true). Keyword-only search active.")
            return

        if self._model is not None:
            return

        with self._load_lock:
            if self._model is not None:
                return

            cache_dir = _resolve_cache_dir()
            logger.info(f"Loading model: {self.MODEL_NAME}")
            logger.info(f"Cache dir: {cache_dir}")

            # Ensure the cache directory exists so HF doesn't try to create
            # symlinks in a non-existent path.
            os.makedirs(cache_dir, exist_ok=True)

            try:
                self._load_with_snapshot(cache_dir)
            except Exception as exc:
                logger.error(f"Model load failed: {exc}", exc_info=True)
                self._model = None

    def _load_with_snapshot(self, cache_dir: str) -> None:
        """
        Load model directly using SentenceTransformer.

        This avoids downloading:
        - ONNX exports (~2.4GB)
        - OpenVINO exports (~0.5GB)
        - TensorFlow weights (~0.4GB)

        and only downloads the files actually needed for inference.
        """

        logger.info(f"Loading model: {self.MODEL_NAME}")

        model = SentenceTransformer(
            self.MODEL_NAME,
            cache_folder=cache_dir,
            device="cpu",
        )

        model.eval()
        self._model = model

        logger.info("✅ Model loaded successfully on CPU.")

    def is_model_loaded(self) -> bool:
        return self._model is not None

    # ── Single embedding ──────────────────────────────────────────────────────

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate a single embedding.

        Thread-safe: concurrent callers queue on _infer_lock so they never
        share the same numpy buffer inside model.encode().
        """
        if self.DISABLE:
            return None

        if self._model is None:
            self.load_model()
        if self._model is None:
            logger.error("Model unavailable — returning None.")
            return None

        if not text or not text.strip():
            logger.warning("Empty text — skipping embedding.")
            return None

        if len(text) > self.MAX_TEXT_CHARS:
            text = text[: self.MAX_TEXT_CHARS]
            logger.warning("Text truncated to %d chars.", self.MAX_TEXT_CHARS)

        t0 = time.time()
        try:
            with self._infer_lock:
                vec = self._model.encode(
                    text,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                )
            elapsed = (time.time() - t0) * 1000
            logger.info("Embedding generation took %.2fms", elapsed)
            if elapsed > self.WARN_LATENCY_MS:
                logger.warning("Embedding exceeded %dms: %.2fms", self.WARN_LATENCY_MS, elapsed)
            return vec.tolist()
        except Exception as exc:
            logger.error("Embedding generation failed: %s", exc, exc_info=True)
            return None

    # ── Batch embeddings ──────────────────────────────────────────────────────

    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for a list of texts in one locked call.
        """
        if self._model is None:
            logger.error("Model not loaded — cannot batch embed.")
            return [None] * len(texts)

        valid_texts: List[str] = []
        valid_idx:   List[int] = []

        for i, t in enumerate(texts):
            if t and t.strip():
                valid_texts.append(t[: self.MAX_TEXT_CHARS])
                valid_idx.append(i)
            else:
                logger.warning("Empty text at index %d — skipped.", i)

        if not valid_texts:
            return [None] * len(texts)

        try:
            with self._infer_lock:
                vecs = self._model.encode(
                    valid_texts,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                )
            results: List[Optional[List[float]]] = [None] * len(texts)
            for i, vec in zip(valid_idx, vecs):
                results[i] = vec.tolist()
            return results
        except Exception as exc:
            logger.error("Batch embedding failed: %s", exc, exc_info=True)
            return [None] * len(texts)


# ── Global singleton ──────────────────────────────────────────────────────────
embedding_generator = EmbeddingGenerator()

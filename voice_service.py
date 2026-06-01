import os
import wave
import json
import logging
import tempfile
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class VoiceService:
    """
    Thread-safe offline Hindi STT using Vosk.

    Concurrency design:
    - _load_lock : ensures only ONE thread loads the Vosk Model object.
                   Other threads wait, then reuse the loaded model.
    - KaldiRecognizer is created fresh per transcribe() call — it is
      stateful (decoder state) and must NEVER be shared across threads.
    - The Vosk Model object itself is read-only after loading and IS
      thread-safe to share — multiple KaldiRecognizers can use it
      simultaneously without any lock.

    Concurrency limit:
    - Vosk Model: unlimited concurrent readers (read-only, thread-safe)
    - KaldiRecognizer: one per request, no sharing needed
    - Effective limit: CPU cores × ~1 transcription/second per core
    - For vosk-model-small-hi-0.22: ~500ms per 5-second audio clip
    - Practical limit: ~4-8 concurrent transcriptions on a 4-core server
    """

    _instance: Optional["VoiceService"] = None
    _model = None
    _model_loaded: bool = False

    MODEL_SEARCH_PATHS = [
        Path(__file__).parent / "vosk-model-small-hi-0.22",
        Path(__file__).parent / "KisanAPI-Backend" / "vosk-model-small-hi-0.22",
        Path.home() / "vosk-model-small-hi-0.22",
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialised"):
            return
        self._initialised = True
        self._load_lock = threading.Lock()  # prevents double-loading

    def load_model(self) -> bool:
        """
        Load Vosk Hindi model exactly once, even under concurrent calls.
        Uses double-checked locking pattern.
        """
        # Fast path — already loaded
        if self._model_loaded:
            return True

        with self._load_lock:
            # Double-check after acquiring lock
            if self._model_loaded:
                return True

            env_path = os.getenv("VOSK_MODEL_PATH")
            search_paths = (
                [Path(env_path)] + self.MODEL_SEARCH_PATHS
                if env_path
                else self.MODEL_SEARCH_PATHS
            )

            model_path = next((p for p in search_paths if p.exists()), None)

            if model_path is None:
                logger.warning(
                    "Vosk Hindi model not found. Voice transcription unavailable. "
                    "Download vosk-model-small-hi-0.22 from https://alphacephei.com/vosk/models "
                    "and place it in the project root."
                )
                return False

            try:
                from vosk import Model, SetLogLevel
                SetLogLevel(-1)
                self._model = Model(str(model_path))
                self._model_loaded = True
                logger.info(f"Vosk Hindi model loaded from: {model_path}")
                return True
            except ImportError:
                logger.error("vosk package not installed. Run: pip install vosk")
                return False
            except Exception as e:
                logger.error(f"Failed to load Vosk model: {e}")
                return False

    def is_model_loaded(self) -> bool:
        return self._model_loaded

    def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> Optional[str]:
        """
        Transcribe audio bytes to Hindi text.

        Thread-safe: each call creates its own KaldiRecognizer instance
        and its own temp file — no shared mutable state between threads.
        The underlying Vosk Model object is read-only and safe to share.

        Args:
            audio_bytes:  WAV file bytes (16-bit, mono, 16kHz recommended)
            sample_rate:  Fallback sample rate if WAV header is unreadable

        Returns:
            Transcribed text, or None on failure / empty audio
        """
        if not self._model_loaded:
            if not self.load_model():
                return None

        tmp_path = None
        try:
            from vosk import KaldiRecognizer

            # Each thread writes its own temp file — no sharing
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            with wave.open(tmp_path, "rb") as wf:
                actual_rate = wf.getframerate()

                if wf.getnchannels() != 1:
                    logger.warning("Audio has %d channels; expected mono.", wf.getnchannels())
                if wf.getsampwidth() != 2:
                    logger.warning("Audio sample width %d bytes; expected 2 (16-bit).", wf.getsampwidth())

                # Fresh KaldiRecognizer per call — stateful, never shared
                rec = KaldiRecognizer(self._model, actual_rate)
                rec.SetWords(True)

                parts = []
                while True:
                    data = wf.readframes(4000)
                    if not data:
                        break
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        if result.get("text"):
                            parts.append(result["text"])

                final = json.loads(rec.FinalResult())
                if final.get("text"):
                    parts.append(final["text"])

            transcript = " ".join(parts).strip()
            logger.info(f"Transcription: '{transcript}'")
            return transcript or None

        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            return None
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass


# Global singleton
voice_service = VoiceService()

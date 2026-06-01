"""
WSGI config for kisan project.
"""

import os

# ── Must be set BEFORE huggingface_hub / sentence_transformers are imported ──
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("HF_HOME",
                      os.path.join(_project_root, ".cache", "huggingface"))
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME",
                      os.path.join(_project_root, ".cache", "sentence_transformers"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kisan.settings")

application = get_wsgi_application()

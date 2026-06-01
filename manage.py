#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# ── Must be set BEFORE huggingface_hub / sentence_transformers are imported ──
# Point HF cache to a project-local folder to avoid Windows symlink issues.
_project_root = os.path.dirname(os.path.abspath(__file__))
_hf_cache = os.path.join(_project_root, ".cache", "huggingface")
os.environ.setdefault("HF_HOME", _hf_cache)
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME",
                      os.path.join(_project_root, ".cache", "sentence_transformers"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kisan.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

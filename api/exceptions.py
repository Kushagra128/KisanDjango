"""
api/exceptions.py

Custom DRF exception handler — returns consistent JSON error responses
to match the FastAPI behaviour the chatbot HTML already expects.
"""

import logging

from rest_framework.views import exception_handler
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Wraps DRF's default handler.
    - Preserves DRF's standard error format for known exceptions.
    - Falls back to a generic 500 JSON body for unknown exceptions.
    """
    response = exception_handler(exc, context)

    if response is not None:
        return response

    # Unhandled exception — log it and return a generic 500
    request = context.get("request")
    path = str(request.build_absolute_uri()) if request else "unknown"
    logger.error("Unhandled exception at %s: %s", path, exc, exc_info=True)

    return Response(
        {
            "message": "Internal server error",
            "error": str(exc),
            "path": path,
        },
        status=500,
    )

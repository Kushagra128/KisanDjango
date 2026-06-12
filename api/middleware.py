"""
api/middleware.py

Request ID middleware — injects a unique X-Request-ID into every request
for cross-system tracing in logs and responses.
"""

import logging
import threading
import uuid

logger = logging.getLogger(__name__)

_request_id_local = threading.local()


def get_request_id() -> str:
    """Return the current request's ID, or 'none' if outside a request."""
    return getattr(_request_id_local, "value", "none")


class RequestIdMiddleware:
    """
    Django middleware that:
    1. Generates a UUID for each incoming request
    2. Stores it in a thread-local for use in log messages
    3. Returns it in the X-Request-ID response header
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get("HTTP_X_REQUEST_ID", str(uuid.uuid4()))
        _request_id_local.value = request_id

        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response

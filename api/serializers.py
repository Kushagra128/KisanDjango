"""
api/serializers.py

DRF serializers — direct port of the FastAPI Pydantic schemas in schema.py.
"""

from rest_framework import serializers
from .models import Solution


class SolutionSerializer(serializers.ModelSerializer):
    """Full Solution record, with optional runtime-only fields."""

    # These three fields are set at runtime by services.py and are never stored.
    similarity_score = serializers.FloatField(read_only=True, default=None, allow_null=True)
    search_method = serializers.CharField(read_only=True, default=None, allow_null=True)
    detected_crop = serializers.CharField(read_only=True, default=None, allow_null=True)

    class Meta:
        model = Solution
        fields = ["id", "problem", "solution", "cropname",
                  "similarity_score", "search_method", "detected_crop"]


class SearchRequestSerializer(serializers.Serializer):
    """Body for POST /search."""

    q = serializers.CharField(min_length=1, help_text="Search query in Hindi or English")


class HealthSerializer(serializers.Serializer):
    """Response for GET /health."""

    status = serializers.CharField()
    model_loaded = serializers.BooleanField()
    database_connected = serializers.BooleanField()
    voice_model_loaded = serializers.BooleanField(default=False)


class VoiceResponseSerializer(serializers.Serializer):
    """Response for POST /voice."""

    transcript = serializers.CharField()
    success = serializers.BooleanField()
    message = serializers.CharField(required=False, allow_null=True)

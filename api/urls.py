"""
api/urls.py

URL routing — maps every endpoint to its view class.

FastAPI route → Django path:
  GET  /               → ChatbotView
  GET  /health         → HealthView
  POST /init-db        → InitDbView
  POST /generate-embeddings → GenerateEmbeddingsView
  GET  /all            → AllCropsView
  GET  /search         → SearchView (GET)
  POST /search         → SearchView (POST)
  POST /voice          → VoiceView
  POST /voice-search   → VoiceSearchView
"""

from django.urls import path
from . import views
from . import metrics

urlpatterns = [
    path("", views.ChatbotView.as_view(), name="chatbot"),
    path("health", views.HealthView.as_view(), name="health"),
    path("init-db", views.InitDbView.as_view(), name="init-db"),
    path("generate-embeddings", views.GenerateEmbeddingsView.as_view(), name="generate-embeddings"),
    path("all", views.AllCropsView.as_view(), name="all-crops"),
    path("search", views.SearchView.as_view(), name="search"),
    path("voice", views.VoiceView.as_view(), name="voice"),
    path("voice-search", views.VoiceSearchView.as_view(), name="voice-search"),
    path("metrics", metrics.MetricsView.as_view(), name="metrics"),
]

"""
api/metrics.py

Lightweight Prometheus-compatible metrics endpoint.
Exposes: search/voice request counts, latency, error rates, model status.
"""

import time
import threading
from collections import defaultdict

from django.http import JsonResponse
from rest_framework.views import APIView

from embedding_service import embedding_generator
from voice_service import voice_service


# ── In-process metric counters ─────────────────────────────────────────────────

class MetricsCollector:
    """Thread-safe in-memory metric store."""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: dict[str, int] = defaultdict(int)
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._gauges: dict[str, float] = {}

    def inc(self, name: str, value: int = 1):
        with self._lock:
            self._counters[name] += value

    def observe(self, name: str, value: float):
        with self._lock:
            self._histograms[name].append(value)
            # Keep only last 1000 observations
            if len(self._histograms[name]) > 1000:
                self._histograms[name] = self._histograms[name][-1000:]

    def set_gauge(self, name: str, value: float):
        with self._lock:
            self._gauges[name] = value

    def snapshot(self) -> dict:
        with self._lock:
            result = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
            }
            # Compute percentiles for histograms
            for name, values in self._histograms.items():
                if values:
                    sorted_vals = sorted(values)
                    n = len(sorted_vals)
                    result[f"{name}_p50"] = sorted_vals[int(n * 0.50)]
                    result[f"{name}_p95"] = sorted_vals[int(n * 0.95)]
                    result[f"{name}_p99"] = sorted_vals[min(int(n * 0.99), n - 1)]
                    result[f"{name}_avg"] = sum(values) / n
                    result[f"{name}_count"] = n
            return result


# Global metrics singleton
metrics = MetricsCollector()


# ── Timing context manager ─────────────────────────────────────────────────────

class MetricTimer:
    """Context manager that records latency when exiting."""

    def __init__(self, metric_name: str, counter_name: str | None = None):
        self.metric_name = metric_name
        self.counter_name = counter_name or f"{metric_name}_total"
        self._start: float = 0.0

    def __enter__(self):
        self._start = time.time()
        return self

    def __exit__(self, *args):
        elapsed_ms = (time.time() - self._start) * 1000
        metrics.observe(f"{self.metric_name}_latency_ms", elapsed_ms)
        metrics.inc(self.counter_name)


# ── Metrics view ───────────────────────────────────────────────────────────────

class MetricsView(APIView):
    """GET /metrics — expose current metrics as JSON."""

    def get(self, request):
        # Update live gauges
        metrics.set_gauge("model_loaded", 1 if embedding_generator.is_model_loaded() else 0)
        metrics.set_gauge("voice_model_loaded", 1 if voice_service.is_model_loaded() else 0)

        return JsonResponse(metrics.snapshot())

"""
api/admin.py

Django admin panel for the Kisan AI pesti_comp database.

Features (as specified in FASTAPI_VS_DJANGO.md § 11):
  List view:
    - Columns: id, cropname, problem preview (80 chars), solution preview (60 chars),
               embedding status (✅/❌), problem length
    - Right sidebar: filter by cropname, filter by embedding status
    - Search bar: cropname, problem, solution
    - Default order: cropname ASC, id ASC
    - 50 records per page

  Detail view:
    - Editable: cropname, problem, solution
    - Read-only: embedding status badge (never shows raw floats)
    - Auto-regenerate embedding when problem changes on save

  Bulk actions:
    - Generate embeddings for selected records
    - Export selected records to CSV (UTF-8-BOM for Excel compatibility)

  Dashboard:
    - Custom AdminSite with summary stats on the home page
"""

import csv
import logging

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils.html import format_html

from .models import Solution

logger = logging.getLogger(__name__)


# ── Custom AdminSite — adds dashboard stats ───────────────────────────────────

class KisanAdminSite(AdminSite):
    site_header = "🌾 Kisan AI Admin"
    site_title = "Kisan AI"
    index_title = "Database Management"

    def index(self, request, extra_context=None):
        """Inject database stats into the admin home page."""
        extra_context = extra_context or {}
        try:
            total = Solution.objects.count()
            with_emb = Solution.objects.exclude(embedding=None).count()
            missing_emb = total - with_emb
            pct = round(with_emb / total * 100, 1) if total else 0

            # Top 5 crops by record count
            top_crops = (
                Solution.objects.values("cropname")
                .annotate(count=Count("id"))
                .order_by("-count")[:5]
            )

            extra_context["kisan_stats"] = {
                "total": total,
                "with_emb": with_emb,
                "missing_emb": missing_emb,
                "pct": pct,
                "top_crops": list(top_crops),
            }
        except Exception as exc:
            logger.warning("Could not fetch dashboard stats: %s", exc)
            extra_context["kisan_stats"] = None

        return super().index(request, extra_context)


kisan_admin_site = KisanAdminSite(name="kisan_admin")


# ── Embedding status filter ───────────────────────────────────────────────────

class EmbeddingStatusFilter(admin.SimpleListFilter):
    title = "Embedding Status"
    parameter_name = "embedding_status"

    def lookups(self, request, model_admin):
        return [
            ("has", "✅ Has Embedding"),
            ("missing", "❌ Missing Embedding"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "has":
            return queryset.exclude(embedding=None)
        if self.value() == "missing":
            return queryset.filter(embedding=None)
        return queryset


# ── SolutionAdmin ─────────────────────────────────────────────────────────────

@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):

    # ── List view ─────────────────────────────────────────────────────────────
    list_display = [
        "id",
        "cropname",
        "problem_preview",
        "solution_preview",
        "embedding_status",
        "problem_length",
    ]
    list_filter = ["cropname", EmbeddingStatusFilter]
    search_fields = ["cropname", "problem", "solution"]
    ordering = ["cropname", "id"]
    list_per_page = 50
    actions = ["generate_embeddings_action", "export_csv_action"]

    # ── Detail view ───────────────────────────────────────────────────────────
    readonly_fields = ["embedding_status"]
    fields = ["cropname", "problem", "solution", "embedding_status"]

    # ── Custom list columns ───────────────────────────────────────────────────

    def problem_preview(self, obj):
        return obj.problem[:80] + "…" if len(obj.problem) > 80 else obj.problem

    problem_preview.short_description = "Problem"

    def solution_preview(self, obj):
        return obj.solution[:60] + "…" if len(obj.solution) > 60 else obj.solution

    solution_preview.short_description = "Solution"

    def embedding_status(self, obj):
        if obj.embedding is not None:
            return format_html(
                '<span style="color:green;font-weight:bold">✅ Generated</span>'
            )
        return format_html(
            '<span style="color:red;font-weight:bold">❌ Missing</span>'
        )

    embedding_status.short_description = "Embedding"

    def problem_length(self, obj):
        return len(obj.problem)

    problem_length.short_description = "Length"
    problem_length.admin_order_field = None  # non-DB field; not sortable via ORM

    # ── Bulk action: generate embeddings ─────────────────────────────────────

    @admin.action(description="Generate embeddings for selected records")
    def generate_embeddings_action(self, request, queryset):
        from embedding_service import embedding_generator

        if not embedding_generator.is_model_loaded():
            embedding_generator.load_model()

        if not embedding_generator.is_model_loaded():
            self.message_user(
                request,
                "❌ Embedding model not loaded. Check server logs.",
                level="error",
            )
            return

        updated = failed = 0
        for obj in queryset:
            try:
                text_for_embedding = f"{obj.cropname} {obj.problem}"
                emb = embedding_generator.generate_embedding(text_for_embedding)
                if emb:
                    obj.embedding = emb
                    # Use update_fields to skip the pre_save signal (avoid double-encode)
                    Solution.objects.filter(pk=obj.pk).update(embedding=emb)
                    updated += 1
                else:
                    failed += 1
            except Exception as exc:
                logger.error("Embedding failed for id=%s: %s", obj.pk, exc)
                failed += 1

        msg = f"✅ Generated embeddings for {updated} record(s)."
        if failed:
            msg += f"  ⚠️ Failed: {failed}."
        self.message_user(request, msg)

    # ── Bulk action: export CSV ───────────────────────────────────────────────

    @admin.action(description="Export selected records to CSV")
    def export_csv_action(self, request, queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = 'attachment; filename="pesti_comp.csv"'

        writer = csv.writer(response)
        writer.writerow(["id", "cropname", "problem", "solution", "has_embedding"])

        for obj in queryset:
            writer.writerow(
                [obj.id, obj.cropname, obj.problem, obj.solution, obj.embedding is not None]
            )

        return response

    # ── Auto-regenerate embedding on detail-view save ─────────────────────────

    def save_model(self, request, obj, form, change):
        """
        When 'problem' or 'cropname' changes in the admin detail view,
        regenerate the embedding before saving.
        The pre_save signal on the model handles this automatically,
        but we add an explicit message so the admin user sees feedback.
        """
        regenerated = False

        if change and ("problem" in form.changed_data or "cropname" in form.changed_data):
            from embedding_service import embedding_generator

            if embedding_generator.is_model_loaded():
                text_for_embedding = f"{obj.cropname} {obj.problem}"
                emb = embedding_generator.generate_embedding(text_for_embedding)
                if emb:
                    obj.embedding = emb
                    regenerated = True
                    logger.info("Admin save: regenerated embedding for id=%s", obj.pk)

        super().save_model(request, obj, form, change)

        if regenerated:
            self.message_user(request, "✅ Embedding regenerated for this record.")

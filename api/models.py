"""
api/models.py

Django ORM model for the existing `pesti_comp` table.

Key design decisions:
  - managed = False  → Django will NOT create/drop this table.
                       The table already exists and is owned by Alembic/manual SQL.
                       Set managed = True only after you are confident you want
                       Django migrations to own the schema.
  - VectorField      → from pgvector-django; stores 384-dim embeddings.
  - Event signals    → replicate the SQLAlchemy before_insert / before_update
                       logic: auto-generate embeddings when a record is saved.
"""

import logging

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from pgvector.django import VectorField

logger = logging.getLogger(__name__)


class Solution(models.Model):
    """Crop problem → solution record, mirroring the `pesti_comp` PostgreSQL table."""

    problem = models.TextField()
    solution = models.TextField()
    cropname = models.CharField(max_length=500, db_index=True)
    embedding = VectorField(dimensions=768, null=True, blank=True)

    class Meta:
        db_table = "pesti_comp"
        managed = False          # Don't let Django touch the existing table schema
        ordering = ["cropname", "id"]
        verbose_name = "Solution"
        verbose_name_plural = "Solutions"

    def __str__(self):
        return f"{self.cropname}: {self.problem[:60]}"


# ── Signals: auto-generate / regenerate embeddings on save ───────────────────

@receiver(pre_save, sender=Solution)
def auto_generate_embedding(sender, instance, **kwargs):
    """
    Regenerate embedding when:
      - new record (instance.pk is None)
      - problem field changed on an existing record
    """
    from embedding_service import embedding_generator

    is_new = instance.pk is None

    if not is_new:
        # Check if `problem` changed by comparing with DB copy
        try:
            db_copy = Solution.objects.get(pk=instance.pk)
            problem_changed = db_copy.problem != instance.problem
        except Solution.DoesNotExist:
            problem_changed = True  # record not in DB yet
    else:
        problem_changed = True

    if not (is_new or problem_changed):
        return  # nothing to regenerate

    if not instance.problem or not instance.problem.strip():
        logger.warning("Empty problem field — setting embedding to None.")
        instance.embedding = None
        return

    try:
        text_for_embedding = f"{instance.cropname} {instance.problem}"
        emb = embedding_generator.generate_embedding(text_for_embedding)
        if emb:
            instance.embedding = emb
            logger.info(
                "Embedding generated for Solution pk=%s cropname='%s'",
                instance.pk or "(new)",
                instance.cropname,
            )
        else:
            logger.warning("Embedding generation returned None for pk=%s", instance.pk)
    except Exception as exc:
        logger.error("Embedding generation failed: %s", exc, exc_info=True)
        # Allow save to proceed without embedding

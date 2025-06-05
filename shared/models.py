from django.utils import timezone

from django.db import models
import uuid


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class ChronoModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class UUIDChronoModel(UUIDModel, ChronoModel):
    class Meta:
        abstract = True

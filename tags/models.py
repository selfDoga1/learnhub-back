import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from taggit.models import TagBase, GenericUUIDTaggedItemBase, TaggedItemBase

class UUIDTag(TagBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    def __str__(self):
        return self.name


class UUIDTaggedItem(GenericUUIDTaggedItemBase, TaggedItemBase):
    """
    Modelo intermediário para ligar as tags (UUIDTag) aos objetos taggeados.
    Usado no through do TaggableManager.
    """
    tag = models.ForeignKey(UUIDTag, related_name="tagged_items", on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")


class RelatedTag(models.Model):
    """
    Relação manual entre tags: indica que uma tag está relacionada manualmente a outra.
    """
    tag = models.ForeignKey(UUIDTag, related_name="manual_relations", on_delete=models.CASCADE)
    related = models.ForeignKey(UUIDTag, related_name="manually_related_to", on_delete=models.CASCADE)

    class Meta:
        unique_together = ('tag', 'related')
        verbose_name = "Related Tag"
        verbose_name_plural = "Related Tags"

    def __str__(self):
        return f"{self.tag.name} → {self.related.name}"


class TagCorrelation(models.Model):
    """
    Correlação automática entre tags, com peso para indicar a força da relação.
    """
    source = models.ForeignKey(UUIDTag, on_delete=models.CASCADE, related_name="correlation_source")
    target = models.ForeignKey(UUIDTag, on_delete=models.CASCADE, related_name="correlation_target")
    weight = models.FloatField(default=0.0)

    class Meta:
        unique_together = ("source", "target")
        verbose_name = "Tag Correlation"
        verbose_name_plural = "Tag Correlations"

    def __str__(self):
        return f"{self.source.name} → {self.target.name} ({self.weight:.2f})"

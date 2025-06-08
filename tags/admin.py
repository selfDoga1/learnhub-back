from django.contrib import admin
from tags.models import UUIDTag, RelatedTag, TagCorrelation


@admin.register(UUIDTag)
class UUIDTagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(RelatedTag)
class RelatedTagAdmin(admin.ModelAdmin):
    list_display = ("tag", "related")
    search_fields = ("tag__name", "related__name")
    list_filter = ("tag", "related")
    autocomplete_fields = ("tag", "related")


@admin.register(TagCorrelation)
class TagCorrelationAdmin(admin.ModelAdmin):
    list_display = ("source", "target", "weight")
    search_fields = ("source__name", "target__name")
    list_filter = ("source", "target")
    autocomplete_fields = ("source", "target")

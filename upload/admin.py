from django.contrib import admin
from django.utils.html import format_html

from .models import ImageUpload


@admin.register(ImageUpload)
class ImageUploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'file_preview', 'created_at')
    search_fields = ('name', 'owner__email')
    readonly_fields = ('file_preview',)
    list_filter = ('owner',)

    def file_preview(self, obj):
        if obj.file:
            return format_html(f'<img src="//localhost:8000/upload/image/{obj.id}/content/" width="100" height="100" style="object-fit: cover;" />')
        return "No Image"

    file_preview.allow_tags = True
    file_preview.short_description = 'Preview'

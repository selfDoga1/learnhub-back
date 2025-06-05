from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver

from core.models import Group
from upload.models import ImageUpload


@receiver(post_delete, sender=ImageUpload)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.file and instance.file.storage.exists(instance.file.name):
        instance.file.delete(save=False)

@receiver(pre_delete, sender=Group)
def delete_cover_image_file(sender, instance, **kwargs):
    cover = instance.cover
    if cover and cover.file and cover.file.storage.exists(cover.file.name):
        cover.file.delete(save=False)
import os
from core.models import UUIDChronoModel
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

FILE_MAX_SIZE = 5 * 1024 * 1024
FILE_EXTENSION_VALIDATOR = FileExtensionValidator(["pdf", "txt"])
IMAGE_EXTENSION_VALIDATOR = FileExtensionValidator(["png", "jpg", "jpeg"])


def validate_file_size(value):
    if value.size > FILE_MAX_SIZE:
        raise ValidationError("O tamanho do arquivo é maior que o permitido")


class BaseFileUpload(UUIDChronoModel):
    file = models.FileField(validators=[validate_file_size, FILE_EXTENSION_VALIDATOR])
    name = models.CharField(max_length=255, blank=True, null=True)
    owner = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True


def upload_to_renamed(instance, filename):
    ext = os.path.splitext(filename)[1]
    new_filename = f"{instance.id}{ext}"
    return f"uploads/{new_filename}"


class ImageUpload(BaseFileUpload):
    file = models.ImageField(validators=[validate_file_size, IMAGE_EXTENSION_VALIDATOR], upload_to=upload_to_renamed)

    def __str__(self):
        return self.name or self.file.name

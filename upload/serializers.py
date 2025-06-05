from rest_framework import serializers

from shared.serializers import DynamicModelSerializer
from .models import ImageUpload


class ImageUploadPublicSerializer(serializers.ModelSerializer):
    uploaded = serializers.BooleanField(read_only=True, default=True)

    class Meta:
        model = ImageUpload
        fields = ['id', 'name', 'uploaded']


class ImageUploadSerializer(DynamicModelSerializer):

    class Meta:
        model = ImageUpload
        fields = '__all__'  # includes 'file' and 'file_url'

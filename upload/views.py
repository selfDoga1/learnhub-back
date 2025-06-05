from django.http import FileResponse
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from adrf.viewsets import GenericViewSet

from rest_framework.decorators import action
from rest_framework import permissions
from django.conf import settings
from django.http.response import HttpResponse
from rest_framework.response import Response
from asgiref.sync import sync_to_async
from .models import ImageUpload
from .serializers import ImageUploadPublicSerializer, ImageUploadSerializer


async def get_file_response(instance):
    if settings.DEBUG:
        response = await sync_to_async(FileResponse)(instance.file, as_attachment=False)
        return response
    else:
        response = HttpResponse()
        response['Content-Type'] = ''
        response['X-Accel-Redirect'] = f'/uploads/{instance.file.name}'
        return response


class ImageUploadViewSet(CreateModelMixin, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = ImageUpload.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return ImageUploadSerializer
        return ImageUploadPublicSerializer

    @action(methods=["get"], detail=True)
    async def content(self, request, *args, **kwargs):
        instance = await sync_to_async(self.get_object)()
        return await get_file_response(instance)

    async def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        await sync_to_async(serializer.save)()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    async def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = await sync_to_async(self.get_object)()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        await sync_to_async(serializer.save)()
        return Response(serializer.data)

    async def retrieve(self, request, *args, **kwargs):
        instance = await sync_to_async(self.get_object)()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    async def destroy(self, request, *args, **kwargs):
        instance = await sync_to_async(self.get_object)()
        await sync_to_async(instance.delete)()
        return Response(status=204)

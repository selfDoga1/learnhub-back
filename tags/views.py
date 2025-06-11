from rest_framework import viewsets, filters
from rest_framework.permissions import IsAdminUser, AllowAny
from .models import RelatedTag, TagCorrelation, UUIDTag
from .serializers import RelatedTagSerializer, TagCorrelationSerializer, UUIDTagSerializer


class RelatedTagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RelatedTag.objects.all()
    serializer_class = RelatedTagSerializer
    permission_classes = [AllowAny]


class TagCorrelationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TagCorrelation.objects.all()
    serializer_class = TagCorrelationSerializer
    permission_classes = [AllowAny]


class UUIDTagViewSet(viewsets.ModelViewSet):
    queryset = UUIDTag.objects.all().order_by('name')
    serializer_class = UUIDTagSerializer
    # permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug']
    ordering_fields = ['name']
    pagination_class = None
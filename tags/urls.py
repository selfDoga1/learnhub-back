from rest_framework.routers import DefaultRouter
from .views import RelatedTagViewSet, TagCorrelationViewSet, UUIDTagViewSet

router = DefaultRouter()
router.register('', UUIDTagViewSet, basename='tags')
router.register(r'related-tags', RelatedTagViewSet, basename='relatedtag')
router.register(r'tag-correlations', TagCorrelationViewSet, basename='tagcorrelation')

urlpatterns = router.urls
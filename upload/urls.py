from rest_framework.routers import DefaultRouter

from upload.views import ImageUploadViewSet

router = DefaultRouter()
router.register(r'image', ImageUploadViewSet)

urlpatterns = router.urls

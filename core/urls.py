from rest_framework.routers import DefaultRouter

from .views import UserViewSet, GroupViewSet, GroupMemberViewSet, ActivityViewSet, PublicViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'public', PublicViewSet, basename='public')
router.register(r'groups', GroupViewSet)
router.register(r'group_members', GroupMemberViewSet)
router.register(r'activities', ActivityViewSet)

urlpatterns = router.urls

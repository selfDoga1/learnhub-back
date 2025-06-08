from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, GroupViewSet, GroupMemberViewSet, ActivityViewSet, PublicViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'groups', GroupViewSet, basename='groups')
router.register(r'group_members', GroupMemberViewSet, basename='group_members')
router.register(r'activities', ActivityViewSet, basename='activity')
router.register(r'public', PublicViewSet, basename='public')


urlpatterns = router.urls

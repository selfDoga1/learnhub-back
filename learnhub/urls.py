from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include
from rest_framework_simplejwt.views import TokenVerifyView, TokenObtainPairView, TokenRefreshView
from shared.views import CookieTokenObtainPairView, LogoutView, CookieTokenRefreshView

urlpatterns = [
    path('', include('core.urls')),
    path('tags/', include('tags.urls')),
    path('upload/', include('upload.urls')),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/logout/', LogoutView.as_view(), name='auth_logout'),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()

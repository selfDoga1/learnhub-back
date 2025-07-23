from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include, re_path
from rest_framework_simplejwt.views import TokenVerifyView, TokenObtainPairView, TokenRefreshView

from react.views import serve_react
from shared.views import CookieTokenObtainPairView, LogoutView, CookieTokenRefreshView

urlpatterns = [
    path('api/', include('core.urls')),
    path('api/tags/', include('tags.urls')),
    path('api/upload/', include('upload.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/logout/', LogoutView.as_view(), name='auth_logout'),
    path('api/admin/', admin.site.urls),
    # Catch-all: serve React
    re_path(r'^(?!api/|admin/)(?P<path>.*)$', serve_react, {"document_root": settings.REACT_APP_BUILD_PATH}),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()

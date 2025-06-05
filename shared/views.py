from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView


class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = serializer.validated_data

        response = Response({'detail': _('User authenticated')}, status=status.HTTP_200_OK)

        access = tokens.get('access')
        refresh = tokens.get('refresh')

        cookie_params = {
            'httponly': True,
            'secure': True,  # Set False in dev if needed
            'samesite': 'Lax',
            'path': '/',
        }

        if access:
            response.set_cookie('access', access, max_age=3600, **cookie_params)
        if refresh:
            response.set_cookie('refresh', refresh, max_age=86400 * 7, **cookie_params)

        return response


class CookieTokenRefreshView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get('refresh')
        response = Response(status=status.HTTP_204_NO_CONTENT)  # No content unless success

        if not refresh:
            response.delete_cookie('access')
            response.delete_cookie('refresh')
            return response

        try:
            serializer = self.get_serializer(data={'refresh': refresh})
            serializer.is_valid(raise_exception=True)
            access = serializer.validated_data.get('access')

            if access:
                response = Response({'detail': 'Token refreshed successfully'}, status=status.HTTP_200_OK)
                response.set_cookie(
                    'access',
                    access,
                    max_age=3600,
                    httponly=True,
                    secure=True,
                    samesite='Lax',
                    path='/',
                )
            return response

        except (InvalidToken, TokenError):
            response.delete_cookie('access')
            response.delete_cookie('refresh')
            return response


class LogoutView(APIView):
    def post(self, request):
        response = Response({'detail': 'Logged out'}, status=status.HTTP_200_OK)
        response.delete_cookie('access')
        response.delete_cookie('refresh')
        return response

from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status

class Custom401SessionAuthentication(SessionAuthentication):
    def authenticate(self, request):
        """
        Returns a `User` if the request session currently has a logged in user.
        Otherwise returns `None` and raises AuthenticationFailed with 401 status.
        """
        result = super().authenticate(request)
        if result is None:
            raise AuthenticationFailed(
                detail='Authentication credentials were not provided.',
                code=status.HTTP_401_UNAUTHORIZED
            )
        return result

class Custom401JWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        """
        Returns a `User` if valid JWT token is provided.
        Otherwise raises AuthenticationFailed with 401 status.
        """
        try:
            return super().authenticate(request)
        except AuthenticationFailed as auth_failed:
            auth_failed.status_code = status.HTTP_401_UNAUTHORIZED
            raise

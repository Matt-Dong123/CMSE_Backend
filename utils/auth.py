from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from user.models import User


class WXOpenIDAuthentication(BaseAuthentication):
    def authenticate(self, request):
        openid = request.META.get('HTTP_X_WX_OPENID')
        if not openid:
            return None
        try:
            user = User.objects.get(openid=openid)
        except User.DoesNotExist:
            raise AuthenticationFailed("未注册用户")
        return user, None

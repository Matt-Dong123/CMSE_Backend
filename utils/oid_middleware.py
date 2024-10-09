from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin

from user.models import User

class WXOpenIDAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        openid = request.META.get('HTTP_X_WX_OPENID')
        if not openid:
            request.user = AnonymousUser()
            return


        try:
            user = User.objects.get(openid=openid)
            request.user = user
        except User.DoesNotExist:
            request.user = AnonymousUser()

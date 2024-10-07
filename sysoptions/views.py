from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


# Create your views here.

@api_view(("GET",))
@permission_classes(permission_classes=(AllowAny,))
def sys_time(request):
    """获取服务器本地时间"""
    data = {"local_time": timezone.localtime()}
    return Response(data)

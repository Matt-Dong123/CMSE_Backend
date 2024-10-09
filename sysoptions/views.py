import logging

import requests
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from sysoptions.models import Files
from user.permissions import PermissionAdmin
from wxcloudrun.settings import ENVID

logger = logging.getLogger(__name__)


# Create your views here.

@api_view(("GET",))
@permission_classes(permission_classes=(AllowAny,))
def sys_time(request):
    """获取服务器本地时间"""

    user = request.user

    data = {"local_time": timezone.localtime()}

    if user.is_authenticated:
        data["user"] = user.username
    else:
        data["user"] = "Anonymous"

    data["meta"] = str(request.META)
    data["oid"] = str(request.META.get("X_WX_OPENID"))

    return Response(data)


@api_view(("GET",))
@permission_classes(permission_classes=(IsAuthenticated, PermissionAdmin))
def get_upload_url(request):
    """获取上传文件的url"""
    path = request.query_params.get("path")
    if not path:
        raise ValidationError({"path": "path is required"})

    payload = {
        "env": ENVID,
        "path": path
    }
    url = f"https://api.weixin.qq.com/tcb/uploadfile"
    print(f"payload: {payload}")
    try:
        response = requests.post(url, json=payload, verify=False)
        response.raise_for_status()
        response = response.json()
        print(f"response: {response}")
        if response["errcode"] != 0:
            raise Exception(response)
        Files.objects.create(file_id=response["file_id"])
    except Exception as e:
        return Response(data={"error": str(e)}, status=500)

    return Response(response)

import logging

import requests
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from sysoptions.models import Files
from sysoptions.serializers import FileUploadSerializer
from wxcloudrun.settings import COS_BUCKET

logger = logging.getLogger(__name__)
# Create your views here.

@api_view(("GET",))
@permission_classes(permission_classes=(AllowAny,))
def sys_time(request):
    """获取服务器本地时间"""
    data = {"local_time": timezone.localtime()}
    return Response(data)


@api_view(("GET",))
@permission_classes(permission_classes=(AllowAny,))
def get_upload_url(request):
    """获取上传文件的url"""
    serializer = FileUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    url = "https://api.weixin.qq.com/tcb/uploadfile"
    payload = {
        "env": COS_BUCKET,
        "path": serializer.validated_data["path"]
    }
    logger.info(f"payload: {payload}")
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        response = response.json()
        logger.info(f"response: {response}")
        if response["errcode"] != 0:
            raise Exception(response.json())
        Files.objects.create(file_id=response.json()["file_id"])
    except Exception as e:
        return Response(data={"error": str(e)}, status=500)

    return Response(response)

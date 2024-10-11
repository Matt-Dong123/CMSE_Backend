import logging

import requests
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from sysoptions.models import Files
from user.permissions import PermissionAdmin
from utils.common_utils import single_upload_file, batch_download_file, batch_delete_file
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
    data["openid"] = str(request.META.get("HTTP_X_WX_OPENID"))

    return Response(data)


@api_view(("GET",))
@permission_classes(permission_classes=(IsAuthenticated, PermissionAdmin))
def get_upload_url(request):
    """获取上传文件的url"""
    path = request.query_params.get("path")
    if not path:
        raise ValidationError({"path": "path is required"})
    ret = single_upload_file(path)
    Files.objects.create(file_id=ret["file_id"])
    return Response(ret)


@api_view(("GET",))
@permission_classes(permission_classes=(AllowAny,))
def get_download_url(request):
    """获取下载文件的url
    : param file_id: 文件id的列表
    """
    file_id = request.query_params.get("file_list")
    if not file_id:
        raise ValidationError({"file_list": "file_id is required"})

    ret = batch_download_file(file_id)
    return Response(ret)

@api_view(("GET",))
@permission_classes(permission_classes=(IsAuthenticated, PermissionAdmin,))
def get_delete_url(request):
    """获取删除文件的url
    : param file_id: 文件id的列表
    """
    file_id = request.query_params.get("fileid_list")
    if not file_id:
        raise ValidationError({"fileid_list": "file_id is required"})

    ret = batch_delete_file(file_id)

    fileids = []
    for it in ret["delete_list"]:
        if it["status"] == 0:
            fileids.append(it["fileid"])

    Files.objects.filter(file_id__in=fileids).delete()

    return Response(ret)


@api_view(("GET",))
@permission_classes(permission_classes=(AllowAny,))
def get_env_id(request):
    return Response({"env_id": ENVID})


import hashlib
import os
import random
from datetime import datetime
from string import ascii_letters, digits
from typing import List

import requests
from django.core.files import File
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from wxcloudrun.settings import TEMP_PATH, ENVID


def is_update(action: str) -> bool:
    """是否是创建或更新动作，包括 create（post）, update（put）, partial_update（patch）

    :param action: create, update, partial_update 等
    :return: 是否是创建或更新动作
    """
    return action in {"create", "update", "partial_update"}


def is_read(action: str) -> bool:
    """读取方法"""
    return action in {"retrieve", "list"}


def is_get_method(request: Request):
    return request.method.upper() == "GET"


def is_post_method(request: Request):
    return request.method.upper() == "POST"


def is_update_method(request: Request):
    return request.method.upper() in {"PUT", "PATCH"}


def to_django_time(dt: datetime):
    dt = dt.isoformat()
    """转换为django时间, 2021-08-01T12:00:00+00.00 -> 2021-08-01 12:00:00"""
    return dt.split("+")[0].replace("T", " ")


def is_write_method(request: Request):
    return request.method.upper() in {"POST", "PUT", "PATCH"}


def fetch_files(
        request: Request,
        verified_file_suffix: List[str] = None,
        file_dir: str = "",
        file_key: str = "file",
):
    """从request中获取文件并下载至Project.MEDIA_ROOT中

    :param request: Request
    :param file_dir: MEDIA_ROOT下的子文件夹名称
    :param verified_file_suffix: 校验文件名的格式后缀
    :param file_key:
    :return: file_paths
    """
    dir_path = TEMP_PATH / file_dir

    os.makedirs(dir_path, exist_ok=True)

    file_paths = []

    for file in request.FILES.getlist(file_key):
        # file: File
        if verified_file_suffix is not None:  # 校验后缀
            idx = file.name.rfind(".")
            suffix: str = file.name[idx + 1:]
            suffix = suffix.lower()
            if idx == -1 or suffix not in verified_file_suffix:
                raise ValidationError(detail=f"{file.name} 格式不符合 {verified_file_suffix}")

        cur_file_path = dir_path / f"{get_file_md5(file)}_{file.name}"
        file_paths.append(str(cur_file_path))

        if os.path.exists(cur_file_path):  # 存在即跳过写入
            continue

        with open(cur_file_path, "wb") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

    return file_paths


def rand_str(length: int) -> str:
    """生成随机字符串

    :param length: 需要的长度
    :return:
    """
    return random.choice(ascii_letters) + "".join(random.sample(ascii_letters + digits, length - 1))


def get_file_md5(file: File) -> str:
    """计算文件md5"""
    md5 = hashlib.md5()
    for chunk in file.chunks():
        md5.update(chunk)
    return md5.hexdigest()


def get_digest_token(token):
    return hashlib.sha256(str(token).encode("utf-8")).hexdigest()


def action_route_helper(action: str, action_map: dict, default=None):
    """根据action获取map中对应值，且可以设置默认值"""
    if action not in action_map and default is None:
        raise APIException(_("action 无匹配且没有设置默认值"))
    return action_map.get(action, default)


def batch_download_file(file_id: List[str], max_age: int = 7200):
    """批量下载文件"""
    payload = {
        "env": ENVID,
        "file_list": [{"fileid": it, "max_age": max_age} for it in file_id]
    }
    url = f"https://api.weixin.qq.com/tcb/batchdownloadfile"

    response = requests.post(url, json=payload, verify=False)
    response.raise_for_status()
    response = response.json()
    if response["errcode"] != 0:
        raise Exception(response)
    return response


def single_upload_file(path: str):
    """上传单个文件"""
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
    except Exception as e:
        return Response(data={"error": str(e)}, status=500)
    return response


def batch_delete_file(file_id: List[str]):
    """批量删除文件"""
    payload = {
        "env": ENVID,
        "fileid_list": file_id
    }
    url = f"https://api.weixin.qq.com/tcb/batchdeletefile"
    response = requests.post(url, json=payload, verify=False)
    response.raise_for_status()
    response = response.json()
    if response["errcode"] != 0:
        raise Exception(response)
    return response


def pairs_generator(num: int):
    """返回数对生成器

    :param num: 总数
    """
    return ((i, j) for i in range(num - 1) for j in range(i + 1, num))

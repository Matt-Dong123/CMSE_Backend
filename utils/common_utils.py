import hashlib
import os
import random
from functools import lru_cache
from string import ascii_letters, digits
from typing import List


from django.core.files import File
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.request import Request

from wxcloudrun.settings import TEMP_PATH


@lru_cache
def is_update(action: str) -> bool:
    """是否是创建或更新动作，包括 create（post）, update（put）, partial_update（patch）

    :param action: create, update, partial_update 等
    :return: 是否是创建或更新动作
    """
    return action in {"create", "update", "partial_update"}


@lru_cache
def is_read(action: str) -> bool:
    """读取方法"""
    return action in {"retrieve", "list"}


def is_get_method(request: Request):
    return request.method.upper() == "GET"


def is_post_method(request: Request):
    return request.method.upper() == "POST"


def is_update_method(request: Request):
    return request.method.upper() in {"PUT", "PATCH"}


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
            suffix: str = file.name[idx + 1 :]
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


@lru_cache
def get_digest_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()




def get_dict_digest(d: dict):
    """dict hash"""
    return hashlib.md5(str(d).encode("utf-8")).hexdigest()


def action_route_helper(action: str, action_map: dict, default=None):
    """根据action获取map中对应值，且可以设置默认值"""
    if action not in action_map and default is None:
        raise APIException(_("action 无匹配且没有设置默认值"))
    return action_map.get(action, default)


def pairs_generator(num: int):
    """返回数对生成器

    :param num: 总数
    """
    return ((i, j) for i in range(num - 1) for j in range(i + 1, num))

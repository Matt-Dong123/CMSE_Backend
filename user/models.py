from django.contrib.auth.models import AbstractUser
from django.db import models

from group.models import Group


def validate_phone(value):
    if len(value) != 11:
        raise ValueError("手机号长度不正确")
    if not value.isdigit():
        raise ValueError("手机号格式不正确")


def validate_stuid(value):
    if len(value) != 10:
        raise ValueError("学号长度不正确")
    if not value.isdigit():
        raise ValueError("学号格式不正确")


'''
先由管理员-> 导入注册信息 -> 学生注册 

'''


class User(AbstractUser):
    openid = models.CharField("OpenID", max_length=30)
    username = models.CharField("学号", max_length=15, unique=True)
    name = models.CharField("姓名", blank=True, max_length=50)
    phone = models.CharField(
        "手机号", max_length=11, validators=[validate_phone]
    )
    isAdmin = models.BooleanField("是否管理员", default=False)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"User: Username={self.username} name={self.name}"

    class Meta:
        db_table = "user"
        ordering = ("-id",)
        verbose_name = "用户"


class Register(models.Model):
    """注册关系"""
    username = models.CharField("学号", max_length=15, unique=True, validators=[validate_stuid])
    name = models.CharField("姓名", max_length=20)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Register: {self.username}"

    class Meta:
        db_table = "register"
        ordering = ("-id",)
        verbose_name = "注册信息"

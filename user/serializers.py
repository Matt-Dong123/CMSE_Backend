from rest_framework import serializers

from group.models import Group
from group.serializers import GroupSerializer
from user.models import Register, User


class RegisterSerializer(serializers.ModelSerializer):
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())

    class Meta:
        model = Register
        fields = "__all__"


class UserOnlyNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("name",)


class UserRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(min_length=10, max_length=10, write_only=True)  # 学号
    name = serializers.CharField(min_length=2, max_length=20, write_only=True)  # 姓名
    phone = serializers.CharField(min_length=11, max_length=11, write_only=True)  # 手机号

    class Meta:
        model = User
        fields = ("id", "username", "name", "phone", "group")
        read_only_fields = ("id",)


class UserProfileSerializer(serializers.ModelSerializer):
    group = GroupSerializer()

    class Meta:
        model = User
        fields = (
            "id",
            "openid",
            "username",
            "name",
            "phone",
            "isAdmin",
            "group",
        )


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())

    class Meta:
        model = User
        fields = (
            "id",
            "openid",
            "username",
            "name",
            "phone",
            "isAdmin",
            "group",
        )
        read_only_fields = (
            "id",
            "openid",
            "username",
            "name",
            "isAdmin",
            "group",
        )


class UserManageSerializer(serializers.ModelSerializer):
    group = GroupSerializer()

    class Meta:
        model = User
        fields = (
            "id",
            "openid",
            "username",
            "name",
            "phone",
            "isAdmin",
            "group",
        )
        read_only_fields = (
            "id",
            "openid",
        )

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from group.models import Group
from group.serializers import GroupSerializer
from user.models import Register, User


class RegisterMixinSerializer(serializers.ModelSerializer):
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())
    name = serializers.CharField(min_length=2, max_length=20)
    username = serializers.CharField(
        min_length=10, max_length=10,
        validators=[UniqueValidator(queryset=Register.objects.all())]
    )

    def validate_username(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("学号格式不正确")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("学号已被注册")
        return value

    class Meta:
        model = Register
        fields = "__all__"


class RegisterUpdateSerializer(RegisterMixinSerializer):
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())

    class Meta:
        model = Register
        fields = "__all__"


class RegisterSerializer(serializers.ModelSerializer):
    group = GroupSerializer()

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

    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("手机号格式不正确")
        if len(value) != 11:
            raise serializers.ValidationError("手机号长度不正确")
        return value

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

    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("手机号格式不正确")
        if len(value) != 11:
            raise serializers.ValidationError("手机号长度不正确")
        return value

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

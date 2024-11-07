from collections import OrderedDict

from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from group.models import Group
from user.models import Register, User
from user.permissions import PermissionAdmin
from user.serializers import RegisterSerializer, UserRegisterSerializer, UserProfileSerializer, \
    UserProfileUpdateSerializer, UserManageSerializer, RegisterUpdateSerializer, UserProfileManageUpdateSerializer
from utils.common_utils import is_get_method, is_update_method


class RegisterManageViewSet(ModelViewSet):
    queryset = Register.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (IsAuthenticated, PermissionAdmin)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("name", "username", "group__name")

    def get_serializer_class(self):
        if is_update_method(self.action):
            return RegisterUpdateSerializer
        return RegisterSerializer

    @action(methods=["post"], detail=False, url_path="batch-register")
    def batch_register(self, request):
        """
        用户信息批量导入注册
        : param username: 学号列表
        : param name: 姓名列表
        : param group: Group ID列表
        """
        try:
            usernames = self.request.data["username"]
            names = self.request.data["name"]
            groupids = self.request.data["group"]
            usernames = list(OrderedDict.fromkeys(usernames))  # 去重
            assert len(usernames) == len(names) == len(groupids), "学号,姓名,班级ID数量不匹配"
        except KeyError:
            raise ValidationError("参数错误")
        except AssertionError as e:
            raise ValidationError(str(e))

        existing_users = (list(User.objects.filter(username__in=usernames).values_list("username", flat=True))
                          + list(Register.objects.filter(username__in=usernames).values_list("username", flat=True)))
        existing_groupids = list(Group.objects.filter(id__in=groupids).values_list("id", flat=True))

        user2create = []

        failed = []
        for username, name, groupid in zip(usernames, names, groupids):
            if not username.isdigit() or len(username) != 10:
                failed.append({"username": username, "reason": "学号格式错误"})
                continue
            if username in existing_users:
                failed.append({"username": username, "reason": "学号已存在"})
                continue
            if groupid not in existing_groupids:
                failed.append({"username": username, "reason": "班级不存在"})
                continue

            user2create.append(Register(username=username, name=name, group_id=groupid))

        Register.objects.bulk_create(user2create)

        return Response(
            data={
                "failed": failed,
                "created": len(user2create)
            },
            status=status.HTTP_201_CREATED
        )


class UserViewSet(GenericViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = RegisterSerializer

    @action(
        methods=["post"],
        detail=False,
        serializer_class=UserRegisterSerializer,
        permission_classes=(AllowAny,),
    )
    def register(self, request, *args, **kwargs):
        """
        用户注册
        : param username: 学号
        : param name: 姓名
        : param phone: 手机号
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        name = serializer.validated_data["name"]
        phone = serializer.validated_data["phone"]
        openid = request.META.get('HTTP_X_WX_OPENID', None)
        if not openid:
            raise ValidationError("未获取到openid")

        try:
            reg_instance = Register.objects.get(username=username, name=name)
            group = reg_instance.group
        except Register.DoesNotExist:
            raise ValidationError("学号和姓名不匹配")

        if User.objects.filter(Q(username=username) | Q(openid=openid)).exists():
            raise ValidationError("当前用户名已被注册或当前openid已经注册")

        with transaction.atomic():
            user = User.objects.create_user(
                openid=openid, username=username, name=name, phone=phone, group=group, password=username, isAdmin=False
            )
            Register.objects.filter(username=username).delete()

        return Response(self.get_serializer(user).data, status=status.HTTP_201_CREATED)

    @action(methods=["get", "put"], detail=False, serializer_class=UserProfileUpdateSerializer)
    def profile(self, request):
        """获取/修改当前用户信息"""
        user = request.user
        if is_get_method(request):
            user_profile = UserProfileSerializer(user).data
            return Response(user_profile)
        elif is_update_method(request):
            serializer = self.get_serializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class UserManageViewSet(mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        mixins.ListModelMixin,
                        GenericViewSet):
    queryset = User.objects.prefetch_related("group")
    permission_classes = (IsAuthenticated, PermissionAdmin)
    serializer_class = UserManageSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = ("username", "name", "phone", "group__name")
    filterset_fields = {
        "username": ["exact", "in"],
        "isAdmin": ["exact"],
        "id": ["gte", "lte", "exact", "gt", "lt", "in"],
        "group_id": ["exact", "in"],
        "group__grade_id": ["exact", "in"],
    }

    def get_serializer_class(self):
        if is_update_method(self.request):
            return UserProfileManageUpdateSerializer
        return UserProfileSerializer

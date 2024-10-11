from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from user.models import Register, User
from user.permissions import PermissionAdmin
from user.serializers import RegisterSerializer, UserRegisterSerializer, UserProfileSerializer
from utils.common_utils import is_get_method, is_update_method


class RegisterManageViewSet(ModelViewSet):
    queryset = Register.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (IsAuthenticated, PermissionAdmin)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("name", "username", "group__name")


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

        user = User.objects.create_user(
            openid=openid, username=username, name=name, phone=phone, group=group, password=username, isAdmin=False
        )

        Register.objects.filter(username=username).delete()

        return Response(self.get_serializer(user).data, status=status.HTTP_201_CREATED)


    @action(methods=["get", "put"], detail=False, serializer_class=UserProfileSerializer)
    def profile(self, request):
        """获取/修改当前用户信息"""
        user = request.user
        if is_get_method(request):
            user_profile = self.get_serializer(user).data
            return Response(user_profile)
        elif is_update_method(request):
            serializer = self.get_serializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

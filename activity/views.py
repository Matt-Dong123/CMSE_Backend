import hashlib
from uuid import uuid1

from django.db.models import Count, Q
from django.utils import timezone
from django_filters import CharFilter, FilterSet, IsoDateTimeFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from activity.models import Activity, Attender
from activity.serializers import ActivityReadSerializer, ActivityUpdateSerializer, AttenderSerializer, \
    ActivityCreateSerializer, ActivityReadDetailSerializer
from sysoptions.views import logger
from user.models import User
from user.permissions import PermissionAdmin, permission_admin
from utils.common_utils import is_update_method, is_post_method, to_django_time


class ActivityFilter(FilterSet):
    start_time = IsoDateTimeFilter(field_name="start_time", lookup_expr="gte")
    end_time = IsoDateTimeFilter(field_name="end_time", lookup_expr="lte")
    status = CharFilter(method='filter_status', help_text="attend: 已经报名的活动, signed: 已签到的活动")

    class Meta:
        model = Activity
        fields = {
            "id": ["gt", "gte", "lt", "lte", "in", "exact"],
            "creator_id": ["exact"],
            "type": ["in", "exact"],
        }

    def filter_status(self, queryset, name, value):
        if value == 'attend':
            return queryset.filter(users=self.request.user)
        elif value == 'signed':
            return queryset.filter(users=self.request.user, attender__status=True)
        else:
            return queryset.filter(end_time__gte=timezone.now())


class ActivityViewSet(ReadOnlyModelViewSet):
    queryset = Activity.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ActivityReadSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = ActivityFilter
    search_fields = (
        "name", "description", "location", "creator__name"
    )

    def get_queryset(self):
        # 管理员可以查看所有活动, 普通用户只能查看自己参与的活动或者未结束的活动
        user = self.request.user
        if permission_admin(self.request):
            return self.queryset.all()
        return self.queryset.filter(Q(users=user) | Q(end_time__gte=timezone.now())).distinct()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ActivityReadDetailSerializer
        return self.serializer_class

    @action(methods=["get"], detail=False, url_path="signin")
    def signin(self, request, *args, **kwargs):
        """
        学生签到
        : param code: 签到码
        """
        if permission_admin(request):
            return Response({"message": "管理员无需签到"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        code = self.request.query_params.get("code")

        try:
            activity = Activity.objects.get(
                sign_code=code, code_expired_time__gte=timezone.now()
            )
            record = Attender.objects.get(activity=activity, user=user)

            if record.status:
                return Response({"message": "您已经签到过了"}, status=status.HTTP_400_BAD_REQUEST)

            record.status = True
            record.sign_time = timezone.now()
            record.save()
            return Response({"message": "签到成功"}, status=status.HTTP_200_OK)

        except Activity.DoesNotExist:
            return Response({"message": "签到码无效或已过期"}, status=status.HTTP_400_BAD_REQUEST)
        except Attender.DoesNotExist:
            return Response({"message": "用户未报名"}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["get"], detail=False, url_path="count_by_type")
    def count_by_type(self, request):
        """按照类型统计活动数量"""
        type_count = Activity.objects.values("type").order_by().annotate(count=Count("type"))
        return Response(type_count, status=200)

    @action(methods=["get"], detail=True, url_path="attend")
    def attend(self, request, *args, **kwargs):
        """参加活动"""
        if permission_admin(request):
            return Response({"message": "管理员无需报名"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        activity = self.get_object()

        if activity.is_started:
            return Response({"message": "活动已开始"}, status=status.HTTP_400_BAD_REQUEST)

        if activity.attender_set.filter(user=user).exists():
            return Response({"message": "您已经报名过了"}, status=status.HTTP_400_BAD_REQUEST)

        if activity.get_attenders_count >= activity.capacity:
            return Response({"message": "报名人数已满"}, status=status.HTTP_400_BAD_REQUEST)

        Attender.objects.create(activity=activity, user=user)
        return Response({"message": "报名成功"})

    @action(methods=["get"], detail=True, url_path="quit")
    def quit(self, request, *args, **kwargs):
        """退出活动"""
        if permission_admin(request):
            return Response({"message": "管理员无需退出"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        activity = self.get_object()

        if activity.is_started:
            return Response({"message": "活动已开始"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            record = Attender.objects.get(activity=activity, user=user)
            record.delete()
            return Response({"message": "退出成功"})
        except Attender.DoesNotExist:
            return Response({"message": "您未报名"}, status=status.HTTP_400_BAD_REQUEST)


class ActivityManageViewSet(ModelViewSet):
    queryset = Activity.objects.prefetch_related("attender_set").all()
    permission_classes = (IsAuthenticated, PermissionAdmin,)
    serializer_class = ActivityReadSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = ActivityFilter
    search_fields = (
        "name", "description", "location", "creator__name"
    )

    def create(self, request, *args, **kwargs):
        request.data["creator"] = request.user.id
        logger.warning(f"User {request.user} create activity {str(request.data)}")
        return super().create(request, *args, **kwargs)

    def get_serializer_class(self):
        if is_post_method(self.request):
            return ActivityCreateSerializer
        elif is_update_method(self.request):
            return ActivityUpdateSerializer
        return self.serializer_class

    @action(methods=["get"], detail=True, url_path="generate_code")
    def generate_code(self, request, *args, **kwargs):
        """
        管理员生成签到码, 每次生成都会覆盖之前的签到码
        : param ttl: 有效时间, 单位秒, 默认10秒
        """
        activity = self.get_object()
        ttl = request.query_params.get("ttl", 10)
        try:
            ttl = int(ttl)
            if ttl <= 0:
                raise ValueError
        except ValueError:
            return Response({"message": "ttl需要为一个正整数"}, status=status.HTTP_400_BAD_REQUEST)
        info = {
            "code": hashlib.md5(str(uuid1()).encode()).hexdigest(),
            "valid_until": to_django_time(timezone.now() + timezone.timedelta(seconds=ttl + 1)),
        }
        activity.sign_code = info["code"]
        activity.code_expired_time = info["valid_until"]
        activity.save(update_fields=("sign_code", "code_expired_time"))

        return Response({**info, "name": activity.name, "id": activity.id})

    @action(methods=['post', 'delete', 'get'], detail=True, url_path="attender")
    def attender(self, request, pk):
        """
        参与活动的用户管理
        如果是POST请求, 则添加用户到活动中
        如果是DELETE请求, 则从活动中删除用户
        如果是GET请求, 则返回活动的参与者



        """
        activity = self.get_object()
        if request.method == 'POST' or request.method == 'DELETE':
            # 添加或删除报名者, 都要先获取用户的id列表
            user = request.data.get("user", None)
            if not user:
                return Response({"message": "user不能为空"}, status=status.HTTP_400_BAD_REQUEST)
            if isinstance(user, str):
                user = [user]
            if not isinstance(user, list):
                return Response({"message": "user需要为一个用户名列表"}, status=status.HTTP_400_BAD_REQUEST)
            users = list(User.objects.filter(username__in=user, isAdmin=False).values_list("id", flat=True))
            count = Attender.objects.filter(activity=activity, user_id__in=users).delete()

            # 删除操作直接返回
            if request.method == 'DELETE':
                return Response({"count": count}, status=status.HTTP_204_NO_CONTENT)

            # 添加操作, 通过bulk_create批量添加
            count = Attender.objects.bulk_create(
                [Attender(activity=activity, user_id=user, status=True) for user in users]
            )
            return Response({"count": count}, status=status.HTTP_201_CREATED)

        elif request.method == 'GET':
            queryset = activity.attender_set.all()
            page = self.paginate_queryset(queryset)
            serializer = AttenderSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

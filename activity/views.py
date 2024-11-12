import hashlib
from uuid import uuid1

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django_filters import CharFilter, FilterSet, IsoDateTimeFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from activity.models import Activity, Attender, ActivityType
from activity.serializers import ActivityReadSerializer, ActivityUpdateSerializer, AttenderSerializer, \
    ActivityCreateSerializer, ActivityReadDetailSerializer, AttenderCreateSerializer, AttenderUpdateSerializer
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
        elif value == 'running':
            return queryset.filter(end_time__gte=timezone.now())
        elif value == "unsigned":
            return queryset.filter(users=self.request.user, attender__status=False)
        else:
            return queryset


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
            ret = {
                "name": activity.name,
                "id": activity.id,
            }
            if record.status:
                return Response({"message": "您已经签到过了"}, status=status.HTTP_400_BAD_REQUEST)

            record.status = True
            record.sign_time = timezone.now()
            record.save()
            return Response({"message": "签到成功", **ret}, status=status.HTTP_200_OK)

        except Activity.DoesNotExist:
            return Response({"message": "签到码无效或已过期"}, status=status.HTTP_400_BAD_REQUEST)
        except Attender.DoesNotExist:
            return Response({"message": "用户未报名当前活动"}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["get"], detail=False, url_path="count_by_type")
    def count_by_type(self, request):
        """按照类型统计活动数量"""
        total_counts = Activity.objects.values("type").order_by().annotate(count=Count("type"))
        total = {activity['type']: activity['count'] for activity in total_counts}

        running_counts = Activity.objects.filter(
            end_time__gte=timezone.now()).values("type").order_by().annotate(count=Count("type"))
        running = {activity['type']: activity['count'] for activity in running_counts}

        user = request.user
        attend_counts = Attender.objects.filter(user=user).values('activity__type').annotate(count=Count('id'))
        attend = {attend['activity__type']: attend['count'] for attend in attend_counts}

        signed_counts = Attender.objects.filter(user=user, status=True).values('activity__type').annotate(
            count=Count('id'))
        signed = {signed['activity__type']: signed['count'] for signed in signed_counts}

        activity_types = ActivityType.choices
        total_dict = {key: total.get(key, 0) for key, _ in activity_types}
        attend_dict = {key: attend.get(key, 0) for key, _ in activity_types}
        signed_dict = {key: signed.get(key, 0) for key, _ in activity_types}
        running_dict = {key: running.get(key, 0) for key, _ in activity_types}

        ret = {
            "total": total_dict,
            "attend": attend_dict,
            "signed": signed_dict,
            "running": running_dict,
        }

        return Response(ret, status=200)

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
            if not 5 <= ttl <= 30:
                raise ValueError
        except ValueError:
            return Response({"message": "ttl需要为一个5~30之间的正整数"}, status=status.HTTP_400_BAD_REQUEST)
        info = {
            "code": hashlib.md5(str(uuid1()).encode()).hexdigest(),
            "valid_until": to_django_time(timezone.now() + timezone.timedelta(seconds=ttl + 1)),
            "ttl": ttl,
        }
        activity.sign_code = info["code"]
        activity.code_expired_time = info["valid_until"]
        activity.save(update_fields=("sign_code", "code_expired_time"))

        return Response({**info, "name": activity.name, "id": activity.id})


class ActivityAttendersManageViewSet(ModelViewSet):
    queryset = Attender.objects.prefetch_related("user").all()
    permission_classes = (IsAuthenticated, PermissionAdmin,)
    serializer_class = AttenderSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = {
        "activity_id": ["exact"],
    }
    search_fields = (
        "user__name", "user__username",
    )

    def get_serializer_class(self):
        if is_post_method(self.request):
            return AttenderCreateSerializer
        elif is_update_method(self.request):
            return AttenderUpdateSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data.get("status", False)
        users = serializer.validated_data.get("usernames")
        uids = [user.id for user in users]
        activity = serializer.validated_data.get("activity")
        with transaction.atomic():
            Attender.objects.filter(activity=activity, user__in=users).update(status=new_status)  # 更新已有记录
            unattended_users = User.objects.filter(id__in=uids).exclude(attender__activity=activity)
            Attender.objects.bulk_create(
                [Attender(activity=activity, user=user, status=new_status) for user in unattended_users]
            )
        return Response({"message": "添加成功"}, status=status.HTTP_201_CREATED)

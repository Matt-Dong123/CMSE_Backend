import hashlib
from uuid import uuid1

from django.utils import timezone
from django_filters import CharFilter
from django_filters import FilterSet, IsoDateTimeFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from activity.models import Activity, Attender
from activity.serializers import ActivityReadSerializer, ActivityUpdateSerializer, AttenderSerializer, \
    ActivityCreateSerializer
from sysoptions.views import logger
from user.models import User
from user.permissions import PermissionAdmin, permission_admin
from utils.common_utils import is_update_method, is_post_method, to_django_time


class ActivityFilter(FilterSet):
    start_time = IsoDateTimeFilter(field_name="start_time", lookup_expr="gte")
    end_time = IsoDateTimeFilter(field_name="end_time", lookup_expr="lte")
    status = CharFilter(method='filter_status')

    class Meta:
        model = Activity
        fields = {
            "id": ["gt", "gte", "lt", "lte", "in", "exact"],
            "creator_id": ["exact"],
            "type": ["in", "exact"],
        }

    def filter_status(self, queryset, name, value):
        if value == 'ended':
            return queryset.filter(end_time__lte=timezone.now())
        elif value == 'waiting':
            return queryset.filter(start_time__gte=timezone.now())
        elif value == 'running':
            return queryset.filter(start_time__lte=timezone.now(), end_time__gte=timezone.now())
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
        user = self.request.user
        if self.request.query_params.get("mine", False):
            return self.queryset.filter(users=user)
        return self.queryset

    @action(methods=["get"], detail=False, url_path="signin")
    def signin(self, request, *args, **kwargs):

        if permission_admin(request):
            return Response({"message": "管理员无需签到"}, status=400)

        user = request.user
        code = self.request.query_params.get("code")

        try:
            activity = Activity.objects.get(
                sign_code=code, code_expired_time__gte=timezone.now()
            )
            record = Attender.objects.get(activity=activity, user=user)

            if record.status:
                return Response({"message": "您已经签到过了"}, status=400)

            record.status = True
            record.sign_time = timezone.now()
            record.save()
            return Response({"message": "签到成功"}, status=200)

        except Activity.DoesNotExist:
            return Response({"message": "签到码无效或已过期"}, status=400)
        except Attender.DoesNotExist:
            return Response({"message": "用户未报名"}, status=400)

    @action(methods=["get"], detail=True, url_path="attend")
    def attend(self, request, *args, **kwargs):
        if permission_admin(request):
            return Response({"message": "管理员无需报名"}, status=400)

        user = request.user
        activity = self.get_object()

        if activity.is_started:
            return Response({"message": "活动已开始"}, status=400)

        if activity.attender_set.filter(id=user.id).exists():
            return Response({"message": "您已经报名过了"}, status=400)

        if activity.get_attenders_count >= activity.capacity:
            return Response({"message": "报名人数已满"}, status=400)

        Attender.objects.create(activity=activity, user=user)
        return Response({"message": "报名成功"})


class ActivityManageViewSet(ModelViewSet):
    queryset = Activity.objects.all()
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
        activity = self.get_object()
        ttl = request.query_params.get("ttl", 15)
        try:
            ttl = int(ttl)
            if ttl <= 0:
                raise ValueError
        except ValueError:
            return Response({"message": "ttl需要为一个正整数"}, status=400)
        info = {
            "code": hashlib.md5(str(uuid1()).encode()).hexdigest(),
            "valid_until": to_django_time(timezone.now() + timezone.timedelta(seconds=ttl + 1)),
        }
        activity.sign_code = info["code"]
        activity.code_expired_time = info["valid_until"]
        activity.save(update_fields=("sign_code", "code_expired_time"))

        return Response({**info, "name": activity.name, "id": activity.id})

    @action(methods=["get"], detail=True, url_path="export", serializer_class=AttenderSerializer)
    def export(self, request, pk):
        activity = self.get_object()
        queryset = activity.attender_set.all()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True, url_path="attender")
    def attender(self, request, pk):
        activity = self.get_object()
        user = request.data.get("user", None)
        if not user:
            return Response({"message": "user不能为空"}, status=400)
        user = list(User.objects.filter(username__in=user, isAdmin=False).values_list("id", flat=True))
        if request.method == 'POST':
            Attender.objects.filter(activity=activity, user_id__in=user).delete()
            count = Attender.objects.bulk_create(
                [Attender(activity=activity, user_id=user, status=True) for user in user]
            )
            return Response({"count": count}, status=201)
        elif request.method == 'DELETE':
            count = Attender.objects.filter(activity=activity, user_id__in=user).delete()
            return Response({"count": count}, status=204)
        return Response(status=405)

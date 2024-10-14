from django_filters import CharFilter
from django_filters import FilterSet, IsoDateTimeFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from django.utils import timezone
from activity.models import Activity, Attender
from activity.serializers import ActivitySerializer
from user.permissions import PermissionAdmin, permission_admin


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
    serializer_class = ActivitySerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_class = ActivityFilter
    search_fields = (
        "name", "description", "location", "creator__name"
    )

    @action(methods=["get"], detail=False, url_path="signin")
    def signin(self, request, *args, **kwargs):

        if permission_admin(request):
            return Response({"message": "管理员无需签到"}, status=400)

        user = request.user
        code = self.request.query_params.get("code")
        try:
            activity = Activity.objects.get(
                sign_info__code=code, sign_info__valid_until__gte=timezone.now()
            )
            record = Attender.objects.get(activity=activity, user=user)

            if record.status:
                return Response({"message": "您已经签到过了"}, status=400)

            record.status = True
            record.sign_time = timezone.now()
            record.save()
            return Response({"message": "签到成功"})

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
    serializer_class = ActivitySerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_class = ActivityFilter
    search_fields = (
        "name", "description", "location", "creator__name"
    )

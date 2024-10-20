from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated
from rest_framework_bulk import BulkModelViewSet

from group.models import Grade, Group
from group.serializers import GradeSerializer, GroupSerializer, GroupUpdateSerializer
from user.permissions import PermissionAdmin
from utils.common_utils import is_update


class GradeManageViewSet(BulkModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = (IsAuthenticated, PermissionAdmin)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("name",)


class GroupManageViewSet(BulkModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated, PermissionAdmin)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = (
        "grade__id",
        "grade__name",
    )
    search_fields = ("name",)

    def get_serializer_class(self):
        if is_update(self.action):
            return GroupUpdateSerializer
        return GroupSerializer

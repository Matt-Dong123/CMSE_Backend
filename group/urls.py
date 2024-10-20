from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_bulk.routes import BulkRouter

from group.views import GradeManageViewSet, GroupManageViewSet

user_router = DefaultRouter()

manage_bulk_router = BulkRouter()

manage_router = DefaultRouter()

manage_bulk_router.register("grade", GradeManageViewSet)
manage_bulk_router.register("group", GroupManageViewSet)

urlpatterns = [
    path("manage/", include(manage_bulk_router.urls)),
    path("manage/", include(manage_router.urls)),
    path("", include(user_router.urls)),
]

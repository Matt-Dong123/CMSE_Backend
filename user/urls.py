from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from wxcloudrun.settings import DEBUG

user_router = DefaultRouter()

manage_router = DefaultRouter()

# manage_router.register("log", LogManageViewSet)
# manage_router.register("auditlog", AuditLogViewSet)
# manage_router.register("sys/options", SysOptionManageViewSet)
# manage_router.register("sys/migrations", MigrationRecorderViewSet)
# manage_router.register("sys/contenttypes", ContentTypeViewSet)
# manage_router.register("sys/utils", UtilsViewSet, basename="sys-utils")


urlpatterns = [
    path("manage/", include(manage_router.urls)),
    path("", include(user_router.urls)),
]


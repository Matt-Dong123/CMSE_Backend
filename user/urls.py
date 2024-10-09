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

if DEBUG:
    import debug_toolbar
    from django.conf import settings
    from django.conf.urls.static import static

    from drf_yasg import openapi
    from drf_yasg.views import get_schema_view

    schema_view = get_schema_view(
        openapi.Info(
            title="OJ API",
            default_version="v1",
            description="OJ API文档",
        ),
    )
    urlpatterns += [
        path("admin/", admin.site.urls),
        path(
            "api/docs/",
            schema_view.with_ui("redoc", cache_timeout=0),
            name="schema-redoc",
        ),
        path("__debug__/", include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

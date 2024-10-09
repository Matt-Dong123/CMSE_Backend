"""wxcloudrun URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions

from wxcloudrun.settings import DEBUG

urlpatterns = [
    path("api/", include("activity.urls")),
    path("api/", include("group.urls")),
    path("api/", include("user.urls")),
    path("api/", include("sysoptions.urls")),
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
            description="API文档",
        ),
        permission_classes=[permissions.AllowAny],
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

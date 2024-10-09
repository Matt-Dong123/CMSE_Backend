from __future__ import print_function, unicode_literals

from django.urls import include, path

from utils.rest_framework_bulk.routes import BulkRouter
from .views import FilteredBulkAPIView, SimpleBulkAPIView, SimpleViewSet

router = BulkRouter()
router.register("", SimpleViewSet, "simple")

urlpatterns = [
    path(r"simpleViewSet/", include((router.urls, "simple"), namespace="api")),
    path(r"filtered/", FilteredBulkAPIView.as_view()),
    path(r"simple/", SimpleBulkAPIView.as_view()),
]

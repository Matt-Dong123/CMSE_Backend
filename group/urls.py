from django.urls import include, path
from rest_framework.routers import DefaultRouter

from group.views import GradeManageViewSet, GroupManageViewSet

user_router = DefaultRouter()

manage_router = DefaultRouter()

manage_router.register("grade", GradeManageViewSet)
manage_router.register("group", GroupManageViewSet)

urlpatterns = [
    path("manage/", include(manage_router.urls)),
    path("", include(user_router.urls)),
]

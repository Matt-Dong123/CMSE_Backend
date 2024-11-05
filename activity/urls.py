from django.urls import include, path
from rest_framework.routers import DefaultRouter

from activity.views import ActivityViewSet, ActivityManageViewSet, ActivityAttendersManageViewSet

user_router = DefaultRouter()
user_router.register("activity", ActivityViewSet)

manage_router = DefaultRouter()
manage_router.register("activity", ActivityManageViewSet)
manage_router.register(
    "attender", ActivityAttendersManageViewSet
)

urlpatterns = [
    path("manage/", include(manage_router.urls)),
    path("", include(user_router.urls)),
]

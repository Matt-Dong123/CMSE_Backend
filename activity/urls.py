from django.urls import include, path
from rest_framework.routers import DefaultRouter

from activity.views import ActivityViewSet, ActivityManageViewSet

user_router = DefaultRouter()
user_router.register("activity", ActivityViewSet)

manage_router = DefaultRouter()
manage_router.register("activity", ActivityManageViewSet)




urlpatterns = [
    path("manage/", include(manage_router.urls)),
    path("", include(user_router.urls)),
]

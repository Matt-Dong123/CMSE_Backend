from django.urls import include, path
from rest_framework.routers import DefaultRouter

from user.views import RegisterManageViewSet, UserViewSet

user_router = DefaultRouter()

user_router.register("user", UserViewSet)

manage_router = DefaultRouter()

manage_router.register("register", RegisterManageViewSet)

urlpatterns = [
    path("manage/", include(manage_router.urls)),
    path("", include(user_router.urls)),
]

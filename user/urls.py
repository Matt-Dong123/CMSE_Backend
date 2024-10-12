from django.urls import include, path
from rest_framework.routers import DefaultRouter

from user.views import RegisterManageViewSet, UserViewSet, UserManageViewSet

user_router = DefaultRouter()

user_router.register("user", UserViewSet)

manage_router = DefaultRouter()

manage_router.register("register", RegisterManageViewSet)
manage_router.register("user", UserManageViewSet)
urlpatterns = [
    path("manage/", include(manage_router.urls)),
    path("", include(user_router.urls)),
]

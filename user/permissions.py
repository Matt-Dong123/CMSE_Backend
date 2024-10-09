from rest_framework.permissions import BasePermission
from rest_framework.request import Request


# 接口PERMISSION的访问流程 has_permission -> has_object_permission
# 缓存contest与group数据
# 缓存contest、group、problem数据


def permission_admin(request: Request) -> bool:
    return (
            request.user.is_authenticated and request.user.isAdmin
    )


class PermissionAdmin(BasePermission):
    def has_permission(self, request, view):
        return permission_admin(request)

    def has_object_permission(self, request, view, obj):
        return permission_admin(request)

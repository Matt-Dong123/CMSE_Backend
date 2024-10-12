import copy
from collections.abc import Iterable

from django.db.models import QuerySet
from rest_framework import status
from rest_framework.response import Response

from utils.rest_framework_bulk import BulkUpdateModelMixin

"""
Mixin集合

继承时注意mixin类顺序在前
"""


class QueryOptimizeMixin:
    """优化DRF关联字段的查询，在DRF视图类(ViewSet)中使用


    related_fields：需要预取的关联字段（列表或元组等可迭代对象）
    """

    related_fields = None

    def get_queryset(self):
        """优化外键查询"""
        assert isinstance(self.related_fields, Iterable), "related_fields 非可迭代对象"
        return super().get_queryset().prefetch_related(*self.related_fields)


class CreatorQueryOptimizeMixin(QueryOptimizeMixin):
    """预置creator关联字段优化"""

    related_fields = ("creator",)


class PerfBulkUpdateModelMixin(BulkUpdateModelMixin):
    """ViewSet 使用，批量更新Mixin

    根据字典直接更新所有指定对象（filtered）的字段，无需再在data中指出ID
    若不是字典则转入原有批量更新逻辑（列表对象，含id）
    """

    def bulk_update(self, request, *args, **kwargs):
        if isinstance(request.data, dict):
            partial = kwargs.pop("partial", False)

            # 请求序列化
            request_serializer = self.get_serializer(data=request.data, partial=partial)
            request_serializer.is_valid(raise_exception=True)

            queryset: QuerySet = self.get_objects(request, *args, **kwargs)
            updated_ids = [i["id"] for i in queryset.values("id")]

            def gen_data(request_data: dict, obj_id):
                """在数据中添加id字段"""
                new_data = copy.deepcopy(request_data)
                new_data["id"] = obj_id
                return new_data

            # 批量序列化
            queryset_serializer = self.get_serializer(
                queryset,
                data=[gen_data(request.data, obj_id) for obj_id in updated_ids],
                many=True,
                partial=partial,
            )
            queryset_serializer.is_valid(raise_exception=True)
            self.perform_bulk_update(queryset_serializer)

            data = {
                "count": queryset.count(),  # 总更新对象数量
                "updated_ids": updated_ids,  # 更新的ID列表
            }
            return Response(data=data, status=status.HTTP_200_OK)
        return super().bulk_update(request, *args, **kwargs)

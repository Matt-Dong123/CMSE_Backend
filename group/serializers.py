from rest_framework import serializers
from rest_framework_bulk import BulkSerializerMixin, BulkListSerializer

from group.models import Grade, Group


class GradeSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ("id", "name")


class GroupSerializer(serializers.ModelSerializer):
    grade = GradeSimpleSerializer()

    class Meta:
        model = Group
        fields = "__all__"


class GroupSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("id", "name")


class GradeSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    groups = GroupSimpleSerializer(many=True, read_only=True)

    class Meta:
        model = Grade
        fields = (
            "id",
            "name",
            "groups",
        )
        list_serializer_class = BulkListSerializer


class GroupUpdateSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    grade = serializers.PrimaryKeyRelatedField(queryset=Grade.objects.all())

    class Meta:
        model = Group
        fields = "__all__"
        list_serializer_class = BulkListSerializer

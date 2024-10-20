from rest_framework import serializers
from rest_framework_bulk import BulkSerializerMixin, BulkListSerializer

from group.models import Grade, Group


class GradeSerializer(BulkSerializerMixin,serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = "__all__"
        list_serializer_class = BulkListSerializer

class GroupSerializer(serializers.ModelSerializer):
    grade = GradeSerializer()

    class Meta:
        model = Group
        fields = "__all__"

class GroupUpdateSerializer(BulkSerializerMixin,serializers.ModelSerializer):
    grade = serializers.PrimaryKeyRelatedField(queryset=Grade.objects.all())

    class Meta:
        model = Group
        fields = "__all__"
        list_serializer_class = BulkListSerializer

class GroupManageListSerializer(serializers.ModelSerializer):
    grade = GradeSerializer()

    class Meta:
        model = Group
        fields = ("id", "grade", "name")
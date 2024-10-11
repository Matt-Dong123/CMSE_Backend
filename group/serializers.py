from rest_framework import serializers

from group.models import Grade, Group


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = "__all__"

class GroupSerializer(serializers.ModelSerializer):
    grade = GradeSerializer()

    class Meta:
        model = Group
        fields = "__all__"

class GroupUpdateSerializer(serializers.ModelSerializer):
    grade = serializers.PrimaryKeyRelatedField(queryset=Grade.objects.all())

    class Meta:
        model = Group
        fields = "__all__"

class GroupManageListSerializer(serializers.ModelSerializer):
    grade = GradeSerializer()

    class Meta:
        model = Group
        fields = ("id", "grade", "name")
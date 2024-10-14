from rest_framework import serializers

from activity.models import Activity, Attender
from user.serializers import UserSimpleSerializer


class ActivityMixinSerializer(serializers.ModelSerializer):

    def validate(self, data):
        if data["start_time"] > data["end_time"]:
            raise serializers.ValidationError("开始时间不能大于结束时间")
        return data

    class Meta:
        model = Activity
        fields = (
            "name",
            "description",
            "start_time",
            "end_time",
            "location",
            "capacity",
            "type",
        )


class ActivityReadSerializer(ActivityMixinSerializer):
    creator = UserSimpleSerializer()

    class Meta:
        model = Activity
        fields = (
            "id",
            "name",
            "description",
            "creator",
            "start_time",
            "end_time",
            "location",
            "capacity",
            "type",
            "get_attenders_count",
        )


class ActivityUpdateSerializer(ActivityMixinSerializer):
    class Meta:
        model = Activity
        fields = (
            "name",
            "description",
            "start_time",
            "end_time",
            "location",
            "capacity",
            "type",
        )


class AttenderSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer()

    class Meta:
        model = Attender
        fields = (
            "user",
            "sign_time",
            "status",
        )

from rest_framework import serializers

from activity.models import Activity
from user.serializers import UserProfileSerializer


class ActivitySerializer(serializers.ModelSerializer):
    creator = UserProfileSerializer()

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

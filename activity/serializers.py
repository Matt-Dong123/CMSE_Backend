from rest_framework import serializers

from activity.models import Activity, Attender
from user.models import User
from user.serializers import UserSimpleSerializer


class ActivityReadSerializer(serializers.ModelSerializer):
    creator = UserSimpleSerializer()
    get_attenders_count = serializers.IntegerField()

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


class ActivityReadDetailSerializer(serializers.ModelSerializer):
    creator = UserSimpleSerializer()
    get_attenders_count = serializers.IntegerField()
    get_signed_attenders_count = serializers.IntegerField()
    is_attend = serializers.SerializerMethodField()
    is_signed = serializers.SerializerMethodField()

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
            "get_signed_attenders_count",
            "is_attend",
            "is_signed",
        )

    def get_is_attend(self, obj):
        user = self.context["request"].user
        return user in obj.users.all()

    def get_is_signed(self, obj):
        user = self.context["request"].user
        return user.attender_set.filter(activity=obj, status=True).exists()


class ActivityCreateSerializer(serializers.ModelSerializer):
    creator = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

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
            "creator",
        )


class ActivityUpdateSerializer(serializers.ModelSerializer):
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


class AttenderSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer()

    class Meta:
        model = Attender
        fields = (
            "id",
            "user",
            "sign_time",
            "status",
            "activity",
        )


class AttenderCreateSerializer(serializers.ModelSerializer):
    usernames = serializers.SlugRelatedField(slug_field="username", queryset=User.objects.all(), many=True)
    activity = serializers.PrimaryKeyRelatedField(queryset=Activity.objects.all())
    status = serializers.BooleanField(default=False)


    class Meta:
        model = Attender
        fields = (
            "usernames",
            "activity",
            "status"
        )


class AttenderUpdateSerializer(serializers.ModelSerializer):
    status = serializers.BooleanField()

    class Meta:
        model = Attender
        fields = (
            "status",
        )

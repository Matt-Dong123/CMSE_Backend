from rest_framework import serializers

from sysoptions.models import Files


class FileUploadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Files
        fields = "__all__"
        read_only_fields = ("id", "upload_time")

    def validate(self, data):
        if 'path' not in data:
            raise serializers.ValidationError({"path": "path is required"})
        return data

from rest_framework import serializers
from .models import BackupHistory


class BackupHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupHistory
        fields = ('id', 'file_name', 'created_at', 'size_in_bytes', 'status')


class RestoreUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

from rest_framework import serializers
from .models import UserActivityLog, SystemEventLog


class UserActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivityLog
        fields = ('id', 'user', 'action', 'resource', 'ip_address', 'timestamp')


class SystemEventLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemEventLog
        fields = ('id', 'event_type', 'description', 'timestamp')


class DecryptLogsRequestSerializer(serializers.Serializer):
    user = serializers.IntegerField(required=False)
    start = serializers.DateTimeField(required=False)
    end = serializers.DateTimeField(required=False)
    limit = serializers.IntegerField(required=False, default=100)

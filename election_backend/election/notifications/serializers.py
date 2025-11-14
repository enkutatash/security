from rest_framework import serializers


class SendEmailSerializer(serializers.Serializer):
    to_email = serializers.EmailField(required=False)
    user_id = serializers.IntegerField(required=False)
    subject = serializers.CharField()
    body = serializers.CharField()


class SendSMSSerializer(serializers.Serializer):
    to_phone = serializers.CharField(required=False)
    user_id = serializers.IntegerField(required=False)
    body = serializers.CharField()


class NotificationLogSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user = serializers.IntegerField(required=False)
    message_type = serializers.CharField()
    content = serializers.CharField()
    sent_at = serializers.DateTimeField(read_only=True)

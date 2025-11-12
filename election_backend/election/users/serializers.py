from rest_framework import serializers
from .models import User, MFADevice


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'nid', 'email', 'phone', 'photo', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'nid', 'email', 'phone', 'photo', 'clearance_label', 'is_email_verified', 'is_phone_verified', 'mfa_enabled')


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is not correct')
        return value


class MFASetupSerializer(serializers.Serializer):
    # no input required; endpoint will return secret and provisioning_uri
    pass


class MFAVerifySerializer(serializers.Serializer):
    token = serializers.CharField()

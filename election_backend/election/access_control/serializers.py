from rest_framework import serializers
from .models import Role, Permission, RoleAssignment, RoleChangeRequest, AccessPolicy, SecurityLabel
from users.serializers import UserSerializer
from users.models import User


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name', 'description')


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id', 'name', 'description')


class RoleAssignmentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = RoleAssignment
        fields = ('id', 'role', 'user', 'assigned_at')


class RoleChangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleChangeRequest
        fields = ('id', 'user', 'requested_role', 'reason', 'status', 'created_at', 'processed_at', 'processed_by')
        read_only_fields = ('status', 'created_at', 'processed_at', 'processed_by')


class AccessPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessPolicy
        fields = ('id', 'name', 'description', 'rules')


class SecurityLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityLabel
        fields = ('id', 'name', 'description')

from django.db import models

# Create your models here.
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Admin, Officer, Voter
    description = models.TextField()

class Permission(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()

class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

class AccessPolicy(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    rules = models.JSONField()  # e.g., for ABAC: {role, district, time}

class SecurityLabel(models.Model):
    name = models.CharField(max_length=50)  # Confidential, Internal, Public
    description = models.TextField()


class RoleAssignment(models.Model):
    """Assign a Role to a User."""
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)


class RoleChangeRequest(models.Model):
    REQUESTED = 'requested'
    APPROVED = 'approved'
    REJECTED = 'rejected'

    STATUS_CHOICES = [
        (REQUESTED, 'Requested'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    requested_role = models.ForeignKey(Role, on_delete=models.CASCADE)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey('users.User', null=True, blank=True, related_name='processed_requests', on_delete=models.SET_NULL)

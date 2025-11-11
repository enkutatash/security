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

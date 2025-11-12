# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    nid = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15, unique=True)
    photo = models.ImageField(upload_to='user_photos/', null=True, blank=True)
    clearance_label = models.CharField(max_length=50, default='Public')  # For MAC
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    mfa_enabled = models.BooleanField(default=False)
    # temporary verification codes (6-digit). Persisted so verification endpoints can validate codes.
    email_verification_code = models.CharField(max_length=6, null=True, blank=True)
    phone_verification_code = models.CharField(max_length=6, null=True, blank=True)

class MFADevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    secret = models.CharField(max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)

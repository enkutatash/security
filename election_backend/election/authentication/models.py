from django.db import models

# Create your models here.
class FailedLoginAttempt(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()

class PasswordChangeLog(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)

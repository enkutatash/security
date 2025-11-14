from django.db import models

# Create your models here.
class FailedLoginAttempt(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()

class PasswordChangeLog(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)


class PasswordReset(models.Model):
    """Simple password reset token for dev/testing flows.

    In production you'd use a secure time-limited token and send it by email.
    """
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    code = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"PasswordReset(user={self.user_id}, code={self.code}, used={self.used})"

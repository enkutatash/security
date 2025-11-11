from django.db import models

# Create your models here.
class NotificationLog(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    message_type = models.CharField(max_length=50)  # Email / SMS
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

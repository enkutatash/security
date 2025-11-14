from django.urls import path
from . import views

urlpatterns = [
    path('send-email/', views.SendEmailView.as_view(), name='send-email'),
    path('send-sms/', views.SendSMSView.as_view(), name='send-sms'),
    path('logs/', views.NotificationLogsView.as_view(), name='notification-logs'),
    path('alerts/', views.NotificationsAlertsView.as_view(), name='notification-alerts'),
]

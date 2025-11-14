from django.urls import path
from . import views

urlpatterns = [
    path('user/', views.UserActivityLogsView.as_view(), name='logs-user'),
    path('system/', views.SystemEventLogsView.as_view(), name='logs-system'),
    path('audit-trail/', views.AuditTrailView.as_view(), name='logs-audit-trail'),
    path('decrypt/', views.DecryptLogsView.as_view(), name='logs-decrypt'),
]

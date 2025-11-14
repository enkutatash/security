from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.DashboardOverviewView.as_view(), name='dashboard-overview'),
    path('roles/', views.DashboardRolesView.as_view(), name='dashboard-roles'),
    path('logs/', views.DashboardLogsView.as_view(), name='dashboard-logs'),
    path('backups/', views.DashboardBackupsView.as_view(), name='dashboard-backups'),
    path('alerts/', views.DashboardAlertsView.as_view(), name='dashboard-alerts'),
    path('access-denied/', views.DashboardAccessDeniedView.as_view(), name='dashboard-access-denied'),
]

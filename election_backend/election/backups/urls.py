from django.urls import path
from . import views

urlpatterns = [
    path('', views.BackupsListView.as_view(), name='backups-list'),
    path('manual/', views.ManualBackupView.as_view(), name='backups-manual'),
    path('restore/', views.RestoreView.as_view(), name='backups-restore'),
    path('history/', views.BackupHistoryView.as_view(), name='backups-history'),
]

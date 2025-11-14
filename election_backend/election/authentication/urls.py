from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='auth-login'),
    path('refresh/', views.RefreshTokenView.as_view(), name='auth-refresh'),
    path('logout/', views.LogoutView.as_view(), name='auth-logout'),
    path('lockout-status/', views.LockoutStatusView.as_view(), name='auth-lockout-status'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='auth-reset-password'),
    path('confirm-reset/', views.ConfirmResetView.as_view(), name='auth-confirm-reset'),
]

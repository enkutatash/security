from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='user-register'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='user-verify-email'),
    path('verify-phone/', views.VerifyPhoneView.as_view(), name='user-verify-phone'),
    path('profile/', views.ProfileView.as_view(), name='user-profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='user-change-password'),
    path('setup-mfa/', views.SetupMFAView.as_view(), name='user-setup-mfa'),
    path('verify-mfa/', views.VerifyMFAView.as_view(), name='user-verify-mfa'),
    path('clearance/', views.ClearanceView.as_view(), name='user-clearance'),
]

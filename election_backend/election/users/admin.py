from django.contrib import admin
from .models import User, MFADevice


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = ('id', 'username', 'email', 'phone', 'is_active', 'is_email_verified', 'is_phone_verified', 'mfa_enabled')
	search_fields = ('username', 'email', 'nid', 'phone')


@admin.register(MFADevice)
class MFADeviceAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'created_at')

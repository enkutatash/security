from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from drf_yasg.utils import swagger_auto_schema
from .serializers import (
	LoginSerializer,
	RefreshSerializer,
	LogoutSerializer,
	LockoutStatusSerializer,
	ResetPasswordSerializer,
	ConfirmResetSerializer,
)
from .models import FailedLoginAttempt, PasswordReset, PasswordChangeLog
from users.models import User
import random
from django.utils import timezone
from datetime import timedelta

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken


def _client_ip(request):
	xff = request.META.get('HTTP_X_FORWARDED_FOR')
	if xff:
		return xff.split(',')[0].strip()
	return request.META.get('REMOTE_ADDR')


class LoginView(APIView):
	permission_classes = (AllowAny,)

	@swagger_auto_schema(request_body=LoginSerializer)
	def post(self, request):
		# Accept either username+password or email+password
		data = request.data.copy()
		serializer = TokenObtainPairSerializer(data=data)
		if serializer.is_valid():
			# successful auth
			return Response(serializer.validated_data)

		# authentication failed — record a failed login attempt if user exists
		username = data.get('username') or None
		email = data.get('email') or None
		user = None
		if email:
			user = User.objects.filter(email=email).first()
		elif username:
			user = User.objects.filter(username=username).first()

		if user:
			FailedLoginAttempt.objects.create(user=user, ip_address=_client_ip(request))

		return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class RefreshTokenView(TokenRefreshView):
	# small subclass so swagger request body appears
	@swagger_auto_schema(request_body=RefreshSerializer)
	def post(self, request, *args, **kwargs):
		return super().post(request, *args, **kwargs)


class LogoutView(APIView):
	permission_classes = (AllowAny,)

	@swagger_auto_schema(request_body=LogoutSerializer)
	def post(self, request):
		serializer = LogoutSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		refresh = serializer.validated_data['refresh']
		try:
			token = RefreshToken(refresh)
			token.blacklist()
		except Exception:
			return Response({'detail': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)

		return Response({'detail': 'logged out'})


class LockoutStatusView(APIView):
	permission_classes = (AllowAny,)

	@swagger_auto_schema(request_body=LockoutStatusSerializer)
	def post(self, request):
		serializer = LockoutStatusSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		username = serializer.validated_data.get('username')
		email = serializer.validated_data.get('email')
		user = None
		if email:
			user = User.objects.filter(email=email).first()
		elif username:
			user = User.objects.filter(username=username).first()

		if not user:
			return Response({'locked': False})

		# simple policy: if >=5 failed attempts in last 15 minutes, account is locked
		window = timezone.now() - timedelta(minutes=15)
		attempts = FailedLoginAttempt.objects.filter(user=user, timestamp__gte=window).count()
		locked = attempts >= 5
		return Response({'locked': locked, 'failed_attempts_last_15m': attempts})


class ResetPasswordView(APIView):
	permission_classes = (AllowAny,)

	@swagger_auto_schema(request_body=ResetPasswordSerializer)
	def post(self, request):
		serializer = ResetPasswordSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		email = serializer.validated_data['email']
		user = User.objects.filter(email=email).first()
		if not user:
			# don't reveal whether user exists
			return Response({'detail': 'If the email exists a reset code has been sent.'})

		code = f"{random.randint(0, 999999):06d}"
		PasswordReset.objects.create(user=user, code=code)

		# Development convenience: return the code in response. In prod send via email.
		return Response({'detail': 'reset code generated', 'reset_code': code})


class ConfirmResetView(APIView):
	permission_classes = (AllowAny,)

	@swagger_auto_schema(request_body=ConfirmResetSerializer)
	def post(self, request):
		serializer = ConfirmResetSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		email = serializer.validated_data['email']
		code = serializer.validated_data['code']
		new_password = serializer.validated_data['new_password']

		user = User.objects.filter(email=email).first()
		if not user:
			return Response({'detail': 'invalid code or email'}, status=status.HTTP_400_BAD_REQUEST)

		# find latest matching unused code within 24 hours
		window = timezone.now() - timedelta(hours=24)
		pr = PasswordReset.objects.filter(user=user, code=code, used=False, created_at__gte=window).order_by('-created_at').first()
		if not pr:
			return Response({'detail': 'invalid or expired code'}, status=status.HTTP_400_BAD_REQUEST)

		user.set_password(new_password)
		user.save()
		pr.used = True
		pr.save()

		# log password change
		PasswordChangeLog.objects.create(user=user)

		return Response({'detail': 'password reset successful'})

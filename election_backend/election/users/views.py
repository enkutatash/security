from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import User, MFADevice
from .serializers import (
	RegistrationSerializer,
	UserSerializer,
	ChangePasswordSerializer,
	MFAVerifySerializer,
	VerifyEmailSerializer,
	VerifyPhoneSerializer,
)
from drf_yasg.utils import swagger_auto_schema
import random
import pyotp


def _gen_code():
	return f"{random.randint(0, 999999):06d}"


class RegisterView(APIView):
	permission_classes = (AllowAny,)

	@swagger_auto_schema(request_body=RegistrationSerializer)
	def post(self, request):
		serializer = RegistrationSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		user = serializer.save()

		# generate verification codes (in real app send via email/SMS)
		email_code = _gen_code()
		phone_code = _gen_code()
		user.email_verification_code = email_code
		user.phone_verification_code = phone_code
		user.save()

		# For development we'll return the codes in the response so they can be used to verify.
		return Response({
			'id': user.id,
			'username': user.username,
			'email_verification_code': email_code,
			'phone_verification_code': phone_code,
		}, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
	permission_classes = (AllowAny,)

	@swagger_auto_schema(request_body=VerifyEmailSerializer)
	def post(self, request):
		serializer = VerifyEmailSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		email = serializer.validated_data['email']
		code = serializer.validated_data['code']

		user = get_object_or_404(User, email=email)
		if user.email_verification_code == code:
			user.is_email_verified = True
			user.email_verification_code = None
			user.save()
			return Response({'detail': 'email verified'})
		return Response({'detail': 'invalid code'}, status=status.HTTP_400_BAD_REQUEST)


class VerifyPhoneView(APIView):
	permission_classes = (AllowAny,)

	@swagger_auto_schema(request_body=VerifyPhoneSerializer)
	def post(self, request):
		serializer = VerifyPhoneSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		phone = serializer.validated_data['phone']
		code = serializer.validated_data['code']

		user = get_object_or_404(User, phone=phone)
		if user.phone_verification_code == code:
			user.is_phone_verified = True
			user.phone_verification_code = None
			user.save()
			return Response({'detail': 'phone verified'})
		return Response({'detail': 'invalid code'}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		serializer = UserSerializer(request.user)
		return Response(serializer.data)

	@swagger_auto_schema(request_body=UserSerializer)
	def put(self, request):
		serializer = UserSerializer(request.user, data=request.data, partial=True)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
	permission_classes = (IsAuthenticated,)

	@swagger_auto_schema(request_body=ChangePasswordSerializer)
	def put(self, request):
		serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		request.user.set_password(serializer.validated_data['new_password'])
		request.user.save()
		return Response({'detail': 'password changed'})


class SetupMFAView(APIView):
	permission_classes = (IsAuthenticated,)

	@swagger_auto_schema(request_body=None)
	def post(self, request):
		# generate secret and create an MFADevice (unverified until user verifies)
		secret = pyotp.random_base32()
		device = MFADevice.objects.create(user=request.user, secret=secret)
		totp = pyotp.TOTP(secret)
		provisioning_uri = totp.provisioning_uri(name=request.user.email or request.user.username, issuer_name='ElectionApp')
		return Response({'secret': secret, 'provisioning_uri': provisioning_uri, 'device_id': device.id})


class VerifyMFAView(APIView):
	permission_classes = (IsAuthenticated,)

	@swagger_auto_schema(request_body=MFAVerifySerializer)
	def post(self, request):
		serializer = MFAVerifySerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		token = serializer.validated_data['token']
		# verify against the latest device for the user
		device = MFADevice.objects.filter(user=request.user).order_by('-created_at').first()
		if not device:
			return Response({'detail': 'no mfa device found'}, status=status.HTTP_400_BAD_REQUEST)

		totp = pyotp.TOTP(device.secret)
		if totp.verify(token):
			request.user.mfa_enabled = True
			request.user.save()
			return Response({'detail': 'mfa verified'})
		return Response({'detail': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class ClearanceView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		return Response({'clearance_label': request.user.clearance_label})


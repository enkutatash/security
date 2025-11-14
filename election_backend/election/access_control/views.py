from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone

from .models import Role, Permission, RoleAssignment, RoleChangeRequest, AccessPolicy, SecurityLabel
from .serializers import (
	RoleSerializer,
	PermissionSerializer,
	RoleAssignmentSerializer,
	RoleChangeRequestSerializer,
	AccessPolicySerializer,
	SecurityLabelSerializer,
)


def _user_has_role(user, role_name):
	return RoleAssignment.objects.filter(user=user, role__name__iexact=role_name).exists()


class RolesView(APIView):
	permission_classes = (AllowAny,)

	def get(self, request):
		roles = Role.objects.all()
		serializer = RoleSerializer(roles, many=True)
		return Response(serializer.data)

	@swagger_auto_schema(request_body=RoleSerializer)
	def post(self, request):
		# admin-only
		if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
			return Response({'detail': 'admin privileges required'}, status=status.HTTP_403_FORBIDDEN)

		serializer = RoleSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoleDetailView(APIView):
	permission_classes = (AllowAny,)

	def get(self, request, pk):
		role = get_object_or_404(Role, pk=pk)
		return Response(RoleSerializer(role).data)

	@swagger_auto_schema(request_body=RoleSerializer)
	def put(self, request, pk):
		if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
			return Response({'detail': 'admin privileges required'}, status=status.HTTP_403_FORBIDDEN)
		role = get_object_or_404(Role, pk=pk)
		serializer = RoleSerializer(role, data=request.data, partial=True)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, pk):
		if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
			return Response({'detail': 'admin privileges required'}, status=status.HTTP_403_FORBIDDEN)
		role = get_object_or_404(Role, pk=pk)
		role.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)


class PermissionsView(APIView):
	permission_classes = (AllowAny,)

	def get(self, request):
		perms = Permission.objects.all()
		serializer = PermissionSerializer(perms, many=True)
		return Response(serializer.data)


class AssignRoleView(APIView):
	permission_classes = (IsAuthenticated,)

	@swagger_auto_schema(request_body=RoleAssignmentSerializer)
	def post(self, request):
		# only Admin or Officer
		if not (_user_has_role(request.user, 'Admin') or _user_has_role(request.user, 'Officer')):
			return Response({'detail': 'admin/officer privileges required'}, status=status.HTTP_403_FORBIDDEN)

		serializer = RoleAssignmentSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RequestRoleChangeView(APIView):
	permission_classes = (IsAuthenticated,)

	@swagger_auto_schema(request_body=RoleChangeRequestSerializer)
	def post(self, request):
		data = request.data.copy()
		# ensure the request.user is the requester
		data['user'] = request.user.id
		serializer = RoleChangeRequestSerializer(data=data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApproveRoleChangeView(APIView):
	permission_classes = (IsAuthenticated,)

	@swagger_auto_schema(request_body=RoleChangeRequestSerializer)
	def post(self, request):
		# only Officer can approve
		if not _user_has_role(request.user, 'Officer'):
			return Response({'detail': 'officer privileges required'}, status=status.HTTP_403_FORBIDDEN)

		req_id = request.data.get('id')
		action = request.data.get('action')  # 'approve' or 'reject'
		if not req_id or action not in ('approve', 'reject'):
			return Response({'detail': 'id and action=(approve|reject) required'}, status=status.HTTP_400_BAD_REQUEST)

		r = get_object_or_404(RoleChangeRequest, pk=req_id)
		if r.status != RoleChangeRequest.REQUESTED:
			return Response({'detail': 'request already processed'}, status=status.HTTP_400_BAD_REQUEST)

		if action == 'approve':
			# assign role
			RoleAssignment.objects.create(user=r.user, role=r.requested_role)
			r.status = RoleChangeRequest.APPROVED
		else:
			r.status = RoleChangeRequest.REJECTED

		r.processed_at = timezone.now()
		r.processed_by = request.user
		r.save()
		return Response(RoleChangeRequestSerializer(r).data)


class PoliciesView(APIView):
	permission_classes = (AllowAny,)

	def get(self, request):
		policies = AccessPolicy.objects.all()
		serializer = AccessPolicySerializer(policies, many=True)
		return Response(serializer.data)

	@swagger_auto_schema(request_body=AccessPolicySerializer)
	def post(self, request):
		# admin only
		if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
			return Response({'detail': 'admin privileges required'}, status=status.HTTP_403_FORBIDDEN)

		serializer = AccessPolicySerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LabelsView(APIView):
	permission_classes = (AllowAny,)

	def get(self, request):
		labels = SecurityLabel.objects.all()
		serializer = SecurityLabelSerializer(labels, many=True)
		return Response(serializer.data)

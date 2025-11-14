from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema

from .models import UserActivityLog, SystemEventLog
from .serializers import (
	UserActivityLogSerializer,
	SystemEventLogSerializer,
	DecryptLogsRequestSerializer,
)
from access_control.models import RoleAssignment


def _user_is_admin(user):
	return user.is_authenticated and (user.is_staff or user.is_superuser or RoleAssignment.objects.filter(user=user, role__name__iexact='Admin').exists())


class UserActivityLogsView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		# filter by user, date range, action
		qs = UserActivityLog.objects.all()
		user_id = request.query_params.get('user')
		action = request.query_params.get('action')
		start = request.query_params.get('start')
		end = request.query_params.get('end')
		if user_id:
			qs = qs.filter(user_id=user_id)
		if action:
			qs = qs.filter(action__icontains=action)
		if start:
			qs = qs.filter(timestamp__gte=start)
		if end:
			qs = qs.filter(timestamp__lte=end)

		serializer = UserActivityLogSerializer(qs.order_by('-timestamp'), many=True)
		return Response(serializer.data)


class SystemEventLogsView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		qs = SystemEventLog.objects.all()
		start = request.query_params.get('start')
		end = request.query_params.get('end')
		if start:
			qs = qs.filter(timestamp__gte=start)
		if end:
			qs = qs.filter(timestamp__lte=end)
		serializer = SystemEventLogSerializer(qs.order_by('-timestamp'), many=True)
		return Response(serializer.data)


class AuditTrailView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		# combine role change and assignment logs from RoleChangeRequest and RoleAssignment
		from access_control.models import RoleChangeRequest, RoleAssignment
		rcr = RoleChangeRequest.objects.all().order_by('-created_at')
		rac = RoleAssignment.objects.all().order_by('-assigned_at')
		# serialize both into a simple combined list
		items = []
		for r in rcr:
			items.append({
				'type': 'role_change_request',
				'id': r.id,
				'user': r.user_id,
				'requested_role': r.requested_role_id,
				'status': r.status,
				'created_at': r.created_at,
				'processed_at': r.processed_at,
				'processed_by': getattr(r.processed_by, 'id', None),
			})
		for a in rac:
			items.append({
				'type': 'role_assignment',
				'id': a.id,
				'user': a.user_id,
				'role': a.role_id,
				'assigned_at': a.assigned_at,
			})
		# sort by timestamp-like fields
		items.sort(key=lambda x: x.get('created_at') or x.get('assigned_at'), reverse=True)
		return Response(items)


class DecryptLogsView(APIView):
	permission_classes = (IsAuthenticated,)

	@swagger_auto_schema(request_body=DecryptLogsRequestSerializer)
	def post(self, request):
		# Only admins can request decryption
		if not _user_is_admin(request.user):
			return Response({'detail': 'admin privileges required'}, status=status.HTTP_403_FORBIDDEN)

		# Accept optional filters in the request body
		serializer = DecryptLogsRequestSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		params = serializer.validated_data
		qs = UserActivityLog.objects.order_by('-timestamp')
		user_id = params.get('user')
		start = params.get('start')
		end = params.get('end')
		limit = params.get('limit', 100)

		if user_id:
			qs = qs.filter(user_id=user_id)
		if start:
			qs = qs.filter(timestamp__gte=start)
		if end:
			qs = qs.filter(timestamp__lte=end)

		user_logs = qs[: max(1, int(limit))]

		out = []
		for l in user_logs:
			out.append(f"{l.timestamp.isoformat()} - user={l.user_id} - action={l.action} - resource={l.resource} - ip={l.ip_address}")
		return Response({'decrypted': out})

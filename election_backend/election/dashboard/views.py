from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.shortcuts import get_object_or_404

from access_control.models import Role, RoleChangeRequest, RoleAssignment
from access_control.serializers import RoleSerializer, RoleChangeRequestSerializer
from audit_logs.models import UserActivityLog, SystemEventLog
from backups.views import BACKUP_DIR
from backups.models import BackupHistory
from elections.models import Election
from users.models import User


def _is_admin(user):
	return user.is_authenticated and (user.is_staff or user.is_superuser or RoleAssignment.objects.filter(user=user, role__name__iexact='Admin').exists())


class DashboardOverviewView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		now = timezone.now()
		users_count = User.objects.count()
		roles_count = Role.objects.count()
		pending_requests = RoleChangeRequest.objects.filter(status=RoleChangeRequest.REQUESTED).count()
		active_elections = Election.objects.filter(start_time__lte=now, end_time__gte=now).count()
		recent_events = SystemEventLog.objects.order_by('-timestamp')[:5]
		events = [{'event_type': e.event_type, 'description': e.description, 'timestamp': e.timestamp} for e in recent_events]
		return Response({
			'users_count': users_count,
			'roles_count': roles_count,
			'pending_role_change_requests': pending_requests,
			'active_elections': active_elections,
			'recent_system_events': events,
		})


class DashboardRolesView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		roles = Role.objects.all()
		roles_ser = RoleSerializer(roles, many=True).data
		pending = RoleChangeRequest.objects.filter(status=RoleChangeRequest.REQUESTED).order_by('-created_at')
		pending_ser = RoleChangeRequestSerializer(pending, many=True).data
		return Response({'roles': roles_ser, 'pending_requests': pending_ser})


class DashboardLogsView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		# filterable by query params: user, start, end, limit
		if not _is_admin(request.user):
			return Response({'detail': 'admin privileges required'}, status=403)

		qs = UserActivityLog.objects.order_by('-timestamp')
		user = request.query_params.get('user')
		action = request.query_params.get('action')
		start = request.query_params.get('start')
		end = request.query_params.get('end')
		limit = int(request.query_params.get('limit') or 100)
		if user:
			qs = qs.filter(user_id=user)
		if action:
			qs = qs.filter(action__icontains=action)
		if start:
			qs = qs.filter(timestamp__gte=start)
		if end:
			qs = qs.filter(timestamp__lte=end)
		logs = []
		for l in qs[:limit]:
			logs.append({'timestamp': l.timestamp, 'user': l.user_id, 'action': l.action, 'resource': l.resource, 'ip': l.ip_address})
		return Response({'logs': logs})


class DashboardBackupsView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		if not _is_admin(request.user):
			return Response({'detail': 'admin privileges required'}, status=403)
		# list files and history
		files = []
		for p in sorted(BACKUP_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
			if p.is_file():
				files.append({'file_name': p.name, 'size_in_bytes': p.stat().st_size, 'created_at': p.stat().st_mtime})
		history = BackupHistory.objects.all().order_by('-created_at')[:50]
		hist = [{'file_name': h.file_name, 'created_at': h.created_at, 'size_in_bytes': h.size_in_bytes, 'status': h.status} for h in history]
		return Response({'files': files, 'history': hist})


class DashboardAlertsView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		# recent system events as alerts
		events = SystemEventLog.objects.order_by('-timestamp')[:50]
		out = [{'event_type': e.event_type, 'description': e.description, 'timestamp': e.timestamp} for e in events]
		return Response({'alerts': out})


class DashboardAccessDeniedView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		# returns last access denied reason for a user or general reason
		user = request.query_params.get('user')
		# try to find a recent user activity log with action containing 'denied' or 'access_denied'
		qs = UserActivityLog.objects.filter(action__icontains='denied')
		if user:
			qs = qs.filter(user_id=user)
		last = qs.order_by('-timestamp').first()
		if last:
			return Response({'reason': f"{last.action} on {last.resource} at {last.timestamp}"})

		# fallback: if no active election, voting attempts would be denied due to time
		now = timezone.now()
		active = Election.objects.filter(start_time__lte=now, end_time__gte=now).exists()
		if not active:
			return Response({'reason': 'RuBAC: Outside voting hours'})
		return Response({'reason': 'access denied'})

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema

from .serializers import SendEmailSerializer, SendSMSSerializer, NotificationLogSerializer
from .models import NotificationLog

User = get_user_model()


def _user_is_admin_or_officer(user):
    # simple check: staff or has role 'officer' assigned
    if user.is_superuser or user.is_staff:
        return True
    try:
        return user.roleassignment_set.filter(role__name__iexact='officer').exists()
    except Exception:
        return False


class SendEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=SendEmailSerializer)
    def post(self, request):
        if not _user_is_admin_or_officer(request.user):
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = SendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # resolve recipient
        to_email = data.get('to_email')
        user_id = data.get('user_id')
        if user_id and not to_email:
            try:
                u = User.objects.get(pk=user_id)
                to_email = u.email
            except User.DoesNotExist:
                return Response({'detail': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)

        # DEV: we don't send real email; log and return
        subject = data['subject']
        body = data['body']
        log = NotificationLog.objects.create(
            user=request.user,
            message_type='email',
            content=f"to:{to_email}; subject:{subject}; body:{body}",
        )

        return Response({'ok': True, 'logged_id': log.id})


class SendSMSView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=SendSMSSerializer)
    def post(self, request):
        if not _user_is_admin_or_officer(request.user):
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = SendSMSSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        to_phone = data.get('to_phone')
        user_id = data.get('user_id')
        if user_id and not to_phone:
            try:
                u = User.objects.get(pk=user_id)
                to_phone = getattr(u, 'phone', None)
            except User.DoesNotExist:
                return Response({'detail': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)

        body = data['body']
        log = NotificationLog.objects.create(
            user=request.user,
            message_type='sms',
            content=f"to:{to_phone}; body:{body}",
        )

        return Response({'ok': True, 'logged_id': log.id})


class NotificationLogsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Admins see all logs, others see their own
        qs = NotificationLog.objects.all().order_by('-sent_at')
        if not (request.user.is_superuser or request.user.is_staff):
            qs = qs.filter(user=request.user)

        data = [
            {
                'id': n.id,
                'user': n.user.id if n.user else None,
                'message_type': n.message_type,
                'content': n.content,
                'sent_at': n.sent_at,
            }
            for n in qs[:100]
        ]
        return Response(data)


class NotificationsAlertsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Simple alerts: recent notification logs for user + important system events
        alerts = []
        # include own notification logs
        own_logs = NotificationLog.objects.filter(user=request.user).order_by('-sent_at')[:10]
        for n in own_logs:
            alerts.append({'type': 'notification', 'id': n.id, 'content': n.content, 'when': n.sent_at})

        # include system-level alerts: failed login attempts count in last hour (if model available)
        try:
            from authentication.models import FailedLoginAttempt
            one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
            recent_failed = FailedLoginAttempt.objects.filter(user=request.user, timestamp__gte=one_hour_ago).count()
            if recent_failed:
                alerts.append({'type': 'security', 'severity': 'warning', 'content': f'{recent_failed} failed login attempts in last hour', 'when': one_hour_ago})
        except Exception:
            pass

        return Response(alerts)
from django.shortcuts import render

# Create your views here.

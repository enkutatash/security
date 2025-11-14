from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from pathlib import Path
import shutil
import gzip
import os

from .models import BackupHistory
from .serializers import BackupHistorySerializer, RestoreUploadSerializer


def _is_admin(user):
	return user.is_authenticated and (user.is_staff or user.is_superuser)


BACKUP_DIR = Path(settings.BASE_DIR) / 'backups_files'
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


class BackupsListView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		# list files in backup dir
		files = []
		for p in sorted(BACKUP_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
			if p.is_file():
				files.append({'file_name': p.name, 'size_in_bytes': p.stat().st_size, 'created_at': timezone.datetime.fromtimestamp(p.stat().st_mtime)})
		return Response(files)


class ManualBackupView(APIView):
	permission_classes = (IsAuthenticated,)

	@swagger_auto_schema(request_body=None)
	def post(self, request):
		if not _is_admin(request.user):
			return Response({'detail': 'admin privileges required'}, status=status.HTTP_403_FORBIDDEN)

		# create a compressed copy of the sqlite DB file
		db_path = Path(settings.BASE_DIR) / 'db.sqlite3'
		if not db_path.exists():
			return Response({'detail': 'database file not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
		dest_name = f'db-backup-{timestamp}.sqlite3.gz'
		dest_path = BACKUP_DIR / dest_name
		try:
			with open(db_path, 'rb') as f_in, gzip.open(dest_path, 'wb') as f_out:
				shutil.copyfileobj(f_in, f_out)

			size = dest_path.stat().st_size
			bh = BackupHistory.objects.create(file_name=dest_name, size_in_bytes=size, status='Success')
			return Response({'detail': 'backup created', 'file_name': dest_name, 'size': size}, status=status.HTTP_201_CREATED)
		except Exception as e:
			BackupHistory.objects.create(file_name=str(dest_name), size_in_bytes=0, status=f'Failed: {str(e)}')
			return Response({'detail': 'backup failed', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RestoreView(APIView):
	permission_classes = (IsAuthenticated,)

	@swagger_auto_schema(request_body=RestoreUploadSerializer)
	def post(self, request):
		if not _is_admin(request.user):
			return Response({'detail': 'admin privileges required'}, status=status.HTTP_403_FORBIDDEN)

		serializer = RestoreUploadSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		upload = serializer.validated_data['file']
		# save uploaded file to backups dir
		dest = BACKUP_DIR / upload.name
		with open(dest, 'wb') as out:
			for chunk in upload.chunks():
				out.write(chunk)

		# attempt to restore: if it's a .gz, decompress into db.sqlite3
		try:
			db_path = Path(settings.BASE_DIR) / 'db.sqlite3'
			# backup current DB
			if db_path.exists():
				backup_current = BACKUP_DIR / f'pre-restore-{timezone.now().strftime("%Y%m%d%H%M%S")}.sqlite3'
				shutil.copy2(db_path, backup_current)

			if dest.suffix == '.gz':
				with gzip.open(dest, 'rb') as f_in, open(db_path, 'wb') as f_out:
					shutil.copyfileobj(f_in, f_out)
			else:
				# assume raw sqlite file
				shutil.copy2(dest, db_path)

			size = dest.stat().st_size
			BackupHistory.objects.create(file_name=dest.name, size_in_bytes=size, status='Restored')
			return Response({'detail': 'restore successful', 'restored_file': dest.name})
		except Exception as e:
			return Response({'detail': 'restore failed', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BackupHistoryView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		items = BackupHistory.objects.all().order_by('-created_at')
		serializer = BackupHistorySerializer(items, many=True)
		return Response(serializer.data)


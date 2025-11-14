from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count
from drf_yasg.utils import swagger_auto_schema

from .models import Election, Candidate, Vote
from .serializers import (
    ElectionSerializer,
    CandidateSerializer,
    VoteSerializer,
    CastVoteSerializer,
)
from access_control.models import RoleAssignment


def _user_has_role(user, role_name):
    return RoleAssignment.objects.filter(user=user, role__name__iexact=role_name).exists()


class ElectionsListCreateView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        now = timezone.now()
        elections = Election.objects.filter(start_time__lte=now, end_time__gte=now)
        serializer = ElectionSerializer(elections, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=ElectionSerializer)
    def post(self, request):
        # Admin or Officer
        if not request.user.is_authenticated or not (_user_has_role(request.user, 'Admin') or _user_has_role(request.user, 'Officer')):
            return Response({'detail': 'admin/officer privileges required'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ElectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ElectionDetailView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        election = get_object_or_404(Election, pk=pk)
        return Response(ElectionSerializer(election).data)

    @swagger_auto_schema(request_body=ElectionSerializer)
    def put(self, request, pk):
        # Admin or Officer
        if not request.user.is_authenticated or not (_user_has_role(request.user, 'Admin') or _user_has_role(request.user, 'Officer')):
            return Response({'detail': 'admin/officer privileges required'}, status=status.HTTP_403_FORBIDDEN)
        election = get_object_or_404(Election, pk=pk)
        serializer = ElectionSerializer(election, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        # Admin only
        if not request.user.is_authenticated or not _user_has_role(request.user, 'Admin'):
            return Response({'detail': 'admin privileges required'}, status=status.HTTP_403_FORBIDDEN)
        election = get_object_or_404(Election, pk=pk)
        election.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CandidatesView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, election_id):
        election = get_object_or_404(Election, pk=election_id)
        candidates = Candidate.objects.filter(election=election)
        serializer = CandidateSerializer(candidates, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=CandidateSerializer)
    def post(self, request, election_id):
        # Admin or Officer
        if not request.user.is_authenticated or not (_user_has_role(request.user, 'Admin') or _user_has_role(request.user, 'Officer')):
            return Response({'detail': 'admin/officer privileges required'}, status=status.HTTP_403_FORBIDDEN)
        election = get_object_or_404(Election, pk=election_id)
        data = request.data.copy()
        data['election'] = election.id
        serializer = CandidateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CastVoteView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(request_body=CastVoteSerializer)
    def post(self, request, election_id):
        election = get_object_or_404(Election, pk=election_id)
        now = timezone.now()
        # RuBAC time-restricted: only during election window
        if not (election.start_time <= now <= election.end_time):
            return Response({'detail': 'election is not active'}, status=status.HTTP_400_BAD_REQUEST)

        # check if user already voted in this election
        existing = Vote.objects.filter(voter=request.user, candidate__election=election).exists()
        if existing:
            return Response({'detail': 'user has already voted in this election'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CastVoteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        candidate = serializer.validated_data['candidate']
        if candidate.election_id != election.id:
            return Response({'detail': 'candidate does not belong to election'}, status=status.HTTP_400_BAD_REQUEST)

        vote = Vote.objects.create(voter=request.user, candidate=candidate)
        return Response({'detail': 'vote recorded', 'vote_id': vote.id}, status=status.HTTP_201_CREATED)


class ResultsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, election_id):
        # Admin or Officer
        if not (_user_has_role(request.user, 'Admin') or _user_has_role(request.user, 'Officer')):
            return Response({'detail': 'admin/officer privileges required'}, status=status.HTTP_403_FORBIDDEN)
        election = get_object_or_404(Election, pk=election_id)
        counts = (
            Vote.objects.filter(candidate__election=election)
            .values('candidate')
            .annotate(votes=Count('id'))
            .order_by('-votes')
        )
        # map candidate id to details
        results = []
        for row in counts:
            cand = Candidate.objects.get(pk=row['candidate'])
            results.append({'candidate_id': cand.id, 'candidate_name': cand.name, 'votes': row['votes']})
        return Response({'election': election.id, 'results': results})
from django.shortcuts import render

# Create your views here.

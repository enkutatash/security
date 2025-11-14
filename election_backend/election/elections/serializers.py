from rest_framework import serializers
from .models import Election, Candidate, Vote


class ElectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = ('id', 'name', 'start_time', 'end_time', 'district')


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ('id', 'election', 'name', 'photo')


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ('id', 'voter', 'candidate', 'timestamp')
        read_only_fields = ('id', 'timestamp', 'voter')


class CastVoteSerializer(serializers.Serializer):
    candidate = serializers.PrimaryKeyRelatedField(queryset=Candidate.objects.all())
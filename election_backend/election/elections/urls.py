from django.urls import path
from . import views

urlpatterns = [
    path('', views.ElectionsListCreateView.as_view(), name='elections-list'),
    path('<int:pk>/', views.ElectionDetailView.as_view(), name='election-detail'),
    path('<int:election_id>/candidates/', views.CandidatesView.as_view(), name='election-candidates'),
    path('<int:election_id>/vote/', views.CastVoteView.as_view(), name='election-vote'),
    path('<int:election_id>/results/', views.ResultsView.as_view(), name='election-results'),
]

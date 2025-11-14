from django.urls import path
from . import views

urlpatterns = [
    path('roles/', views.RolesView.as_view(), name='access-roles'),
    path('roles/<int:pk>/', views.RoleDetailView.as_view(), name='access-role-detail'),
    path('permissions/', views.PermissionsView.as_view(), name='access-permissions'),
    path('assign-role/', views.AssignRoleView.as_view(), name='access-assign-role'),
    path('request-role-change/', views.RequestRoleChangeView.as_view(), name='access-request-role-change'),
    path('approve-role-change/', views.ApproveRoleChangeView.as_view(), name='access-approve-role-change'),
    path('policies/', views.PoliciesView.as_view(), name='access-policies'),
    path('labels/', views.LabelsView.as_view(), name='access-labels'),
]

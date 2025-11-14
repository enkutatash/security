"""
URL configuration for election project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions

# swagger
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_yasg.utils import swagger_auto_schema


class SwaggerTokenObtainPairView(TokenObtainPairView):
    """Small subclass that adds an explicit request body schema for drf-yasg.

    drf-yasg sometimes doesn't infer the request body for class-based views
    coming from third-party libs. Decorating post() with swagger_auto_schema
    ensures the Swagger UI shows editable request JSON fields.
    """

    @swagger_auto_schema(request_body=TokenObtainPairSerializer)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

schema_view = get_schema_view(
    openapi.Info(
        title="Election API",
        default_version='v1',
        description="API documentation for Election project",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/auth/', include('authentication.urls')),
    path('api/access/', include('access_control.urls')),
    path('api/elections/', include('elections.urls')),
    path('api/logs/', include('audit_logs.urls')),
    path('api/backups/', include('backups.urls')),

    # JWT token endpoints
    path('api/token/', SwaggerTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Swagger / ReDoc
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger.yaml', schema_view.without_ui(cache_timeout=0), name='schema-yaml'),
]

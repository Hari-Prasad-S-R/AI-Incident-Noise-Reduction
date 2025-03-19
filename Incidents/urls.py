"""
URL configuration for Incidents project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import include, path

from ITSM.models import Incident
from rest_framework import routers, serializers, viewsets
import ITSM.views as views

# Serializers define the API representation.
class IncidentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Incident
        fields = ['id', 'url', 'status', 'title', 'description',  'created_at', 'updated_at']

# ViewSets define the view behavior.
class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'incidents', IncidentViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('ui/', views.incident_list, name='incident_list'),
    path('ui/create/', views.incident_create, name='incident_create'),
    path('ui/<int:incident_id>/edit/', views.incident_edit, name='incident_edit'),
    path('ui/<int:incident_id>/delete/', views.incident_delete, name='incident_delete'),
    path('webhook/incident/', views.webhook_create, name='webhook_create')
]

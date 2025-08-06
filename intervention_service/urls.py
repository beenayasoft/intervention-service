# intervention_service/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.views import APIView
from rest_framework.response import Response

class HealthCheckView(APIView):
    def get(self, request):
        return Response({"status": "ok"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('interventions.urls')),
    path('health/', HealthCheckView.as_view(), name='health'),
]
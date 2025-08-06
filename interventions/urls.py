# interventions/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import views

# 1) Router principal
router = DefaultRouter()
router.register(r'interventions', views.InterventionViewSet, basename='intervention')

# 2) Routes imbriquées
interventions_router = NestedDefaultRouter(
    router, r'interventions', lookup='intervention'
)
interventions_router.register(r'tasks',     views.InterventionTaskViewSet,     basename='intervention-tasks')
interventions_router.register(r'materials', views.InterventionMaterialViewSet, basename='intervention-materials')
interventions_router.register(r'reports',   views.InterventionReportViewSet,   basename='intervention-reports')
interventions_router.register(r'photos',    views.InterventionPhotoViewSet,    basename='intervention-photos')

urlpatterns = [
    # Routes générées par les routers
    path('', include(router.urls)),
    path('', include(interventions_router.urls)),

    # Endpoints Beenaya standards
    path('stats/', views.intervention_stats, name='intervention-stats'),
    path('health/', views.HealthCheckView.as_view(), name='health'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
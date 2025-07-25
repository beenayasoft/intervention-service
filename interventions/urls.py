from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from . import views

router = DefaultRouter()
router.register(r'interventions', views.InterventionViewSet)

# Routers imbriqués pour les ressources liées aux interventions
interventions_router = NestedDefaultRouter(router, r'interventions', lookup='intervention')
interventions_router.register(r'tasks', views.InterventionTaskViewSet, basename='intervention-tasks')
interventions_router.register(r'materials', views.InterventionMaterialViewSet, basename='intervention-materials')
interventions_router.register(r'reports', views.InterventionReportViewSet, basename='intervention-reports')
interventions_router.register(r'photos', views.InterventionPhotoViewSet, basename='intervention-photos')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(interventions_router.urls)),
] 
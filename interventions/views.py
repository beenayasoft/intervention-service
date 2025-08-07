# interventions/views.py
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import (
    Intervention,
    InterventionTask,
    InterventionMaterial,
    InterventionReport,
    InterventionPhoto
)
from .serializers import (
    InterventionSerializer,
    InterventionTaskSerializer,
    InterventionMaterialSerializer,
    InterventionReportSerializer,
    InterventionPhotoSerializer
)
from .pagination import OptimizedPagination


class HealthCheckView(APIView):
    def get(self, request):
        return Response({"status": "ok"})


# 1. ViewSet principal
class InterventionViewSet(viewsets.ModelViewSet):
    """
    CRUD complet sur les interventions
    """
    queryset = Intervention.objects.all()
    serializer_class = InterventionSerializer
    pagination_class = OptimizedPagination

    def get_queryset(self):
        qs = super().get_queryset()
        statut = self.request.query_params.get("statut")
        if statut:
            qs = qs.filter(statut=statut)
        return qs

    @method_decorator(cache_page(30))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="statut",
                description="Filtrer par statut d'intervention",
                required=False,
                type=str
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


# 2. Nested ViewSets
class InterventionTaskViewSet(viewsets.ModelViewSet):
    serializer_class = InterventionTaskSerializer

    def get_queryset(self):
        return InterventionTask.objects.filter(
            intervention_id=self.kwargs['intervention_pk']
        )

    def perform_create(self, serializer):
        serializer.save(intervention_id=self.kwargs['intervention_pk'])


class InterventionMaterialViewSet(viewsets.ModelViewSet):
    serializer_class = InterventionMaterialSerializer

    def get_queryset(self):
        return InterventionMaterial.objects.filter(
            intervention_id=self.kwargs['intervention_pk']
        )

    def perform_create(self, serializer):
        serializer.save(intervention_id=self.kwargs['intervention_pk'])


class InterventionReportViewSet(viewsets.ModelViewSet):
    serializer_class = InterventionReportSerializer

    def get_queryset(self):
        return InterventionReport.objects.filter(
            intervention_id=self.kwargs['intervention_pk']
        )

    def perform_create(self, serializer):
        serializer.save(intervention_id=self.kwargs['intervention_pk'])


class InterventionPhotoViewSet(viewsets.ModelViewSet):
    serializer_class = InterventionPhotoSerializer

    def get_queryset(self):
        return InterventionPhoto.objects.filter(
            intervention_id=self.kwargs['intervention_pk']
        )

    def perform_create(self, serializer):
        serializer.save(intervention_id=self.kwargs['intervention_pk'])


# 3. Endpoint stats
@extend_schema(summary="Statistiques des interventions")
@api_view(["GET"])
@cache_page(30)
def intervention_stats(request):
    stats = (
        Intervention.objects
        .values("statut")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    return Response(stats)
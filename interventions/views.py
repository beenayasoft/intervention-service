from rest_framework import generics
from .models import Intervention
from .serializers import InterventionSerializer

class InterventionListCreateView(generics.ListCreateAPIView):
    queryset = Intervention.objects.all()
    serializer_class = InterventionSerializer

class InterventionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Intervention.objects.all()
    serializer_class = InterventionSerializer

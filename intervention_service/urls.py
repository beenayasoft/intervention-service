from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings

def health_check(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('interventions.urls')),
    path('health/', health_check, name='health_check'),
]

# Ajout de la documentation API en mode développement
# Désactivé temporairement pour résoudre les problèmes
# if settings.DEBUG:
#     from rest_framework.schemas import get_schema_view
#     from rest_framework.documentation import include_docs_urls
#     
#     urlpatterns += [
#         path('docs/', include_docs_urls(
#             title='Intervention Service API',
#             description='API pour la gestion des interventions'
#         )),
#         path('schema/', get_schema_view(
#             title='Intervention Service API',
#             description='API pour la gestion des interventions',
#             version='1.0.0'
#         ), name='openapi-schema'),
#     ] 
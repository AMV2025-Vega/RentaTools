from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def salud(_request):
    """Health-check para Docker/Nginx (no toca la base de datos)."""
    return JsonResponse({"estado": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/salud/", salud, name="salud"),
    path("api/", include("apps.usuarios.presentation.urls")),
    path("api/", include("apps.inventario.presentation.urls")),
    path("api/", include("apps.reservas.presentation.urls")),
    path("api/", include("apps.publico.presentation.urls")),
]

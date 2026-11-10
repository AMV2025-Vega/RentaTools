"""
Vistas del frontend: SOLO entregan plantillas. Los datos los carga el navegador consumiendo
la API REST del propio sistema (API-first), así la UI no depende de los servicios internos.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


def _siguiente(request) -> str:
    """Destino tras iniciar sesión; solo rutas del propio sitio (evita open redirect)."""
    destino = request.GET.get("next", "/")
    ok = url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}, require_https=request.is_secure())
    return destino if ok else "/"


def catalogo(request):
    return render(request, "web/catalogo.html")


def detalle(request, pk):
    return render(request, "web/detalle.html", {"herramienta_id": pk})


@login_required
def mis_reservas(request):
    return render(request, "web/mis_reservas.html")


@login_required
def publicar(request):
    return render(request, "web/publicar.html")


def ingresar(request):
    if request.user.is_authenticated:
        return redirect(_siguiente(request))
    return render(request, "web/ingresar.html", {"siguiente": _siguiente(request)})


def registro(request):
    if request.user.is_authenticated:
        return redirect("/")
    return render(request, "web/registro.html", {"siguiente": _siguiente(request)})

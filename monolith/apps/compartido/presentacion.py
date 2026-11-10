"""
Traducción de excepciones de dominio a respuestas HTTP (capa de presentación).

Es la ÚNICA tabla de mapeo error -> código HTTP del sistema, así las vistas
no contienen lógica de negocio ni decisiones sobre reglas.
"""
import logging

from django.utils import translation
from rest_framework import status
from rest_framework.response import Response

from apps.compartido.excepciones import (
    Conflicto,
    DominioError,
    NoEncontrado,
    Prohibido,
    ReglaNegocioViolada,
    ServicioNoDisponible,
)
from apps.compartido.mensajes_error import mensaje_para
from apps.compartido.puertos import Solicitante

logger = logging.getLogger(__name__)

# Orden importa: de lo más específico a lo más general.
_MAPA_HTTP = (
    (NoEncontrado, status.HTTP_404_NOT_FOUND),
    (ServicioNoDisponible, status.HTTP_503_SERVICE_UNAVAILABLE),
    (Prohibido, status.HTTP_403_FORBIDDEN),
    (Conflicto, status.HTTP_409_CONFLICT),
    (ReglaNegocioViolada, status.HTTP_400_BAD_REQUEST),
)


def respuesta_de_error(exc: DominioError) -> Response:
    """Convierte un error de dominio en Response con el código HTTP adecuado."""
    for clase, codigo_http in _MAPA_HTTP:
        if isinstance(exc, clase):
            return Response({"codigo": exc.codigo, "error": mensaje_para(exc.codigo, exc.mensaje)}, status=codigo_http)
    logger.exception("Error de dominio sin mapeo HTTP: %s", exc)
    return Response({"codigo": exc.codigo, "error": mensaje_para(exc.codigo, exc.mensaje)}, status=status.HTTP_400_BAD_REQUEST)


def solicitante_desde(request) -> Solicitante:
    """Construye el DTO del actor a partir del usuario autenticado."""
    u = request.user
    return Solicitante(id=u.id, nombre=u.get_full_name() or u.get_username(), email=u.email, idioma=translation.get_language() or "")

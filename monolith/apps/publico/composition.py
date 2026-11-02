from django.utils import timezone

from apps.publico.application.services import EstadisticasService
from apps.publico.infrastructure.repositories import DjangoEstadisticasRepository


def construir_estadisticas_service() -> EstadisticasService:
    return EstadisticasService(DjangoEstadisticasRepository(), timezone.now)

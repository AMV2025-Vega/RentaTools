from apps.auditoria.infrastructure.logger import DjangoAuditLogger
from apps.compartido.infraestructura import DjangoTransactionManager
from apps.inventario.application.services import HerramientaService
from apps.inventario.infrastructure.repositories import DjangoHerramientaRepository


def construir_herramienta_service() -> HerramientaService:
    return HerramientaService(DjangoHerramientaRepository(), DjangoAuditLogger(), DjangoTransactionManager())

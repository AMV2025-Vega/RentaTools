"""Composition root: único lugar donde se eligen las implementaciones concretas."""
from apps.auditoria.infrastructure.logger import DjangoAuditLogger
from apps.usuarios.application.services import RegistroUsuarioService
from apps.usuarios.infrastructure.repositories import DjangoUsuarioRepository


def construir_registro_service() -> RegistroUsuarioService:
    return RegistroUsuarioService(DjangoUsuarioRepository(), DjangoAuditLogger())

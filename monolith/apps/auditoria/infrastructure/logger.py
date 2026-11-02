"""Adaptador de auditoría: persiste en PostgreSQL y emite una línea JSON a stdout."""
import json
import logging

from apps.auditoria.models import RegistroAuditoria
from apps.compartido.puertos import AuditLogger, EventoAuditoria

_stdout = logging.getLogger("audit")


class DjangoAuditLogger(AuditLogger):
    """
    Se invoca DENTRO de la transacción del caso de uso: si la transacción
    falla, tampoco queda el registro de un hecho que no ocurrió; los
    rechazos se registran aparte, fuera de la transacción revertida.
    """

    def registrar(self, evento: EventoAuditoria) -> None:
        RegistroAuditoria.objects.create(
            actor_id=evento.actor_id,
            accion=evento.accion,
            entidad=evento.entidad,
            entidad_id=str(evento.entidad_id),
            resultado=evento.resultado,
            detalle=evento.detalle,
        )
        _stdout.info(
            json.dumps(
                {
                    "accion": evento.accion,
                    "entidad": evento.entidad,
                    "entidad_id": str(evento.entidad_id),
                    "resultado": evento.resultado,
                    "actor_id": evento.actor_id,
                    "detalle": evento.detalle,
                },
                default=str,
                ensure_ascii=False,
            )
        )

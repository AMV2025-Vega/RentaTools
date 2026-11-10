from django.db import models


class RegistroAuditoria(models.Model):
    """
    Bitácora inmutable (append-only) de cada transacción relevante.

    - Sin ForeignKey: el registro sobrevive aunque el actor/entidad se elimine
      y el módulo queda desacoplado (extraíble a su propio servicio).
    - La inmutabilidad se garantiza en la BD con un trigger (ver migración 0002).
    """

    ocurrido_en = models.DateTimeField(auto_now_add=True, db_index=True)
    actor_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    accion = models.CharField(max_length=60, db_index=True)
    entidad = models.CharField(max_length=60)
    entidad_id = models.CharField(max_length=60, blank=True)
    resultado = models.CharField(max_length=20)
    detalle = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-ocurrido_en", "-id"]

    def __str__(self):
        return f"{self.ocurrido_en:%Y-%m-%d %H:%M:%S} {self.accion} {self.entidad}#{self.entidad_id} [{self.resultado}]"

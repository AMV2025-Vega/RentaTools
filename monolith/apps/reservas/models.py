"""
Modelo de persistencia de Reservas. Solo campos y restricciones de BD:
la regla "una herramienta no puede estar reservada dos veces en las mismas fechas"
la garantiza PostgreSQL con un ExclusionConstraint (a prueba de condiciones de carrera).
"""
from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeBoundary, RangeOperators
from django.db import models
from django.db.models import F, Func, Q


class DateRange(Func):
    """daterange(fecha_inicio, fecha_fin, '[]'): rango con ambos extremos incluidos."""

    function = "DATERANGE"
    output_field = DateRangeField()


class Reserva(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE_PAGO = "PENDIENTE_PAGO", "Pendiente de pago"
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        CANCELADA = "CANCELADA", "Cancelada"
        FINALIZADA = "FINALIZADA", "Finalizada"

    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reservas")
    herramienta = models.ForeignKey("inventario.Herramienta", on_delete=models.PROTECT, related_name="reservas")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    dias = models.PositiveIntegerField()
    costo_total = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=3, default="COP")
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE_PAGO)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en"]
        constraints = [
            models.CheckConstraint(condition=Q(fecha_fin__gte=F("fecha_inicio")), name="reserva_fechas_ordenadas"),
            ExclusionConstraint(
                name="reserva_sin_solape",
                expressions=[
                    (
                        DateRange("fecha_inicio", "fecha_fin", RangeBoundary(inclusive_lower=True, inclusive_upper=True)),
                        RangeOperators.OVERLAPS,
                    ),
                    ("herramienta", RangeOperators.EQUAL),
                ],
                # Solo bloquean las reservas vigentes; las canceladas liberan las fechas.
                condition=Q(estado__in=["PENDIENTE_PAGO", "CONFIRMADA"]),
            ),
        ]

    def __str__(self):
        return f"Reserva #{self.pk} {self.herramienta_id} {self.fecha_inicio}->{self.fecha_fin} [{self.estado}]"

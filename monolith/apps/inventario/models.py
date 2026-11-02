"""
Modelos de persistencia de Inventario. Intencionalmente "delgados":
solo campos y restricciones de BD. Las reglas de negocio viven en domain/ y application/.
"""
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Herramienta(models.Model):
    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        MANTENIMIENTO = "MANTENIMIENTO", "En mantenimiento"

    propietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="herramientas")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="herramientas")
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio_por_dia = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVA)
    foto_url = models.URLField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en"]
        constraints = [
            models.CheckConstraint(condition=models.Q(precio_por_dia__gt=0), name="herramienta_precio_positivo"),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.estado})"

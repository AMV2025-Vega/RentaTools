from django.contrib import admin

from apps.reservas.models import Reserva


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "herramienta", "fecha_inicio", "fecha_fin", "costo_total", "estado")
    list_filter = ("estado",)

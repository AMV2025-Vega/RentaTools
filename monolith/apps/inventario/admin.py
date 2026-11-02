from django.contrib import admin

from apps.inventario.models import Categoria, Herramienta

admin.site.register(Categoria)


@admin.register(Herramienta)
class HerramientaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "propietario", "categoria", "precio_por_dia", "estado")
    list_filter = ("estado", "categoria")

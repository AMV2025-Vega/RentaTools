from django.contrib import admin

from apps.auditoria.models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    """Solo lectura: la auditoría no se edita desde el admin."""

    list_display = ("ocurrido_en", "accion", "entidad", "entidad_id", "resultado", "actor_id")
    list_filter = ("accion", "resultado")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

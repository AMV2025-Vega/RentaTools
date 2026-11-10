"""
Mensajes de error de la API traducibles con gettext, indexados por `codigo` de dominio.

El dominio lanza errores con un código estable; aquí (presentación) se elige el texto en el
idioma de la petición (cookie `django_language` o cabecera Accept-Language). Si un código no
está en el catálogo se usa el mensaje original del dominio.
"""
from django.utils.translation import gettext_lazy as _

MENSAJES_ERROR = {
    # no encontrado
    "herramienta_no_encontrada": _("La herramienta no existe."),
    "reserva_no_encontrada": _("La reserva no existe."),
    "categoria_no_encontrada": _("La categoría no existe."),
    # reglas de negocio
    "datos_incompletos": _("Usuario y correo son obligatorios."),
    "nombre_obligatorio": _("El nombre de la herramienta es obligatorio."),
    "precio_invalido": _("El precio por día debe ser mayor que cero."),
    "estado_invalido": _("El estado indicado no es válido."),
    "cliente_obligatorio": _("El cliente es obligatorio."),
    "herramienta_obligatoria": _("La herramienta es obligatoria."),
    "herramienta_inactiva": _("La herramienta no está disponible para alquiler."),
    "reserva_propia": _("No puedes reservar tu propia herramienta."),
    "fechas_obligatorias": _("Las fechas de inicio y fin son obligatorias."),
    "fechas_invertidas": _("La fecha de fin no puede ser anterior a la de inicio."),
    "fecha_pasada": _("La fecha de inicio no puede estar en el pasado."),
    "reserva_muy_larga": _("La reserva excede el máximo de días permitido."),
    "reserva_incompleta": _("Faltan datos para construir la reserva."),
    # conflictos
    "username_duplicado": _("El nombre de usuario ya está en uso."),
    "email_duplicado": _("El correo ya está registrado."),
    "herramienta_no_disponible": _("La herramienta ya está reservada en alguna de esas fechas."),
    "no_se_puede_cancelar": _("No se puede cancelar una reserva que ya no está vigente."),
    "estado_reserva_invalido": _("La operación no es válida para el estado actual de la reserva."),
    # permisos
    "no_es_propietario": _("Solo el propietario puede cambiar el estado de la herramienta."),
    "no_es_el_cliente": _("Solo quien hizo la reserva puede cancelarla."),
    "reporte_ajeno": _("Ese reporte pertenece a otro usuario."),
    # infraestructura
    "reportes_no_disponible": _("El servicio de reportes no está disponible en este momento."),
    "servicio_no_disponible": _("El servicio no está disponible en este momento."),
    # autenticación
    "credenciales_invalidas": _("Usuario o contraseña incorrectos."),
}


def mensaje_para(codigo: str, por_defecto: str) -> str:
    """Texto traducido al idioma activo, o el mensaje original si el código no tiene traducción."""
    traducible = MENSAJES_ERROR.get(codigo)
    return str(traducible) if traducible is not None else por_defecto

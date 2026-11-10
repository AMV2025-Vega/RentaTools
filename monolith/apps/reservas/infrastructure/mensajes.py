"""
Catálogo de plantillas de notificación, traducibles con gettext.

El idioma fuente es el español (msgid); las traducciones viven en locale/<idioma>/.
`gettext_noop` marca la cadena para `makemessages` sin traducirla al importar el módulo.
"""
from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext, gettext_noop

PLANTILLAS: dict[str, tuple[str, str]] = {
    "reserva_creada": (
        gettext_noop("Reserva registrada"),
        gettext_noop(
            "Hola %(nombre)s, tu reserva #%(id)s de '%(herramienta)s' (%(inicio)s a %(fin)s) "
            "quedó pendiente de pago por %(total)s %(moneda)s."
        ),
    ),
    "reserva_cancelada": (
        gettext_noop("Reserva cancelada"),
        gettext_noop("Hola %(nombre)s, tu reserva #%(id)s fue cancelada."),
    ),
}


def renderizar(plantilla: str, contexto: dict, idioma: str = "") -> tuple[str, str]:
    """Devuelve (asunto, mensaje) en el idioma pedido (o el del proyecto si no se indica)."""
    asunto_id, cuerpo_id = PLANTILLAS[plantilla]
    idioma = idioma if idioma in dict(settings.LANGUAGES) else settings.LANGUAGE_CODE
    with translation.override(idioma):
        return gettext(asunto_id), gettext(cuerpo_id) % contexto

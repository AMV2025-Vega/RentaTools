"""
Excepciones de dominio compartidas por todos los módulos.

Son Python puro (sin Django ni DRF). La capa de presentación decide
cómo traducirlas a HTTP (ver compartido/presentacion.py). Cada excepción
lleva un `codigo` estable (útil para i18n y para clientes de la API).
"""


class DominioError(Exception):
    """Base de todos los errores de negocio."""

    codigo = "error_dominio"

    def __init__(self, mensaje: str, codigo: str | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        if codigo:
            self.codigo = codigo


class NoEncontrado(DominioError):
    """El recurso solicitado no existe -> HTTP 404."""

    codigo = "no_encontrado"


class ReglaNegocioViolada(DominioError):
    """Los datos son válidos sintácticamente pero violan una regla -> HTTP 400."""

    codigo = "regla_negocio_violada"


class Conflicto(DominioError):
    """El estado actual del sistema impide la operación -> HTTP 409."""

    codigo = "conflicto"


class Prohibido(DominioError):
    """El actor no tiene derecho sobre el recurso -> HTTP 403."""

    codigo = "prohibido"

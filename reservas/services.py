from .domain.reserva_builder import ReservaBuilder
from .infra.notificador_factory import NotificadorFactory

class ReservaService:
    def __init__(self, notificador=None):
        self.notificador = notificador or NotificadorFactory.crear()

    def crear_reserva(self, datos):
        reserva = (ReservaBuilder()
                   .para_herramienta(datos["herramienta_id"])
                   .para_usuario(datos["user_id"])
                   .en_fechas(datos["fecha_inicio"], datos["fecha_fin"])
                   .build())
        reserva.save()
        self.notificador.enviar_confirmacion(reserva)
        return reserva
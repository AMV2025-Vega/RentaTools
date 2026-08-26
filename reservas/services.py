from datetime import date
from typing import List, Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from reservas.models import Cliente, Herramienta, Reserva
from reservas.domain.reserva_builder import ReservaBuilder
from reservas.infra.notificador_factory import NotificadorFactory


class ReservaService:
    """
    Servicio de Aplicación para orquestar los flujos de uso relacionados con las Reservas.
    Cumple con el principio SRP centralizando la lógica de negocio.
    """

    @staticmethod
    @transaction.atomic
    def crear_reserva(
        cliente_id: int,
        herramientas_ids: List[int],
        fecha_inicio: date,
        fecha_fin: date,
        tipo_notificacion: str = "EMAIL"
    ) -> Reserva:
        """
        Orquesta la creación completa de una reserva usando el patrón Builder y notifica al cliente.
        Garantiza atomicidad transaccional.
        """
        # 1. Obtención y validación de entidades del dominio
        try:
            cliente = Cliente.objects.get(pk=cliente_id)
        except Cliente.DoesNotExist:
            raise ObjectDoesNotExist(f"No existe un cliente registrado con el ID {cliente_id}.")

        herramientas = Herramienta.objects.filter(pk__in=herramientas_ids)
        if len(herramientas) != len(herramientas_ids):
            raise ValidationError("Una o más herramientas especificadas no fueron encontradas.")

        # 2. Uso del Patrón Creacional Builder
        builder = ReservaBuilder()
        builder.set_cliente(cliente)
        builder.set_fechas(fecha_inicio, fecha_fin)

        for herramienta in herramientas:
            builder.add_herramienta(herramienta)

        reserva = builder.build()

        # 3. Uso del Patrón Creacional Factory para notificaciones
        notificador = NotificadorFactory.get_notificador(tipo_notificacion)
        mensaje = (
            f"Hola {cliente.nombre}, tu reserva #{reserva.id} ha sido registrada exitosamente "
            f"por un costo total de ${reserva.costo_total}."
        )
        notificador.enviar_confirmacion(cliente.email, mensaje)

        return reserva

    @staticmethod
    @transaction.atomic
    def cancelar_reserva(reserva_id: int) -> Reserva:
        """
        Cancela una reserva y libera el estado de las herramientas asociadas.
        """
        try:
            reserva = Reserva.objects.get(pk=reserva_id)
        except Reserva.DoesNotExist:
            raise ObjectDoesNotExist(f"No existe la reserva con ID {reserva_id}.")

        if reserva.estado == 'CANCELADA':
            raise ValidationError("La reserva ya se encuentra cancelada.")

        if reserva.estado == 'FINALIZADA':
            raise ValidationError("No se puede cancelar una reserva que ya ha finalizado.")

        reserva.estado = 'CANCELADA'
        reserva.save()

        # Liberar estado de las herramientas vinculadas
        for detalle in reserva.detalles.all():
            herramienta = detalle.herramienta
            herramienta.estado = 'DISPONIBLE'
            herramienta.save()

        return reserva


class HerramientaService:
    """
    Servicio de Aplicación para gestionar el catálogo y disponibilidad de herramientas.
    """

    @staticmethod
    def listar_disponibles() -> List[Herramienta]:
        """
        Obtiene las herramientas con estado DISPONIBLE.
        """
        return Herramienta.objects.filter(estado='DISPONIBLE')
from decimal import Decimal
from datetime import date
from django.core.exceptions import ValidationError
from reservas.models import Reserva, DetalleReserva, Cliente, Herramienta


class ReservaBuilder:
    """
    Patrón Creacional Builder para construir paso a paso la entidad Reserva
    garantizando validaciones de negocio antes de persistir.
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self._cliente = None
        self._fecha_inicio = None
        self._fecha_fin = None
        self._herramientas = []
        return self

    def set_cliente(self, cliente: Cliente):
        if not cliente:
            raise ValidationError("El cliente es obligatorio para crear la reserva.")
        self._cliente = cliente
        return self

    def set_fechas(self, fecha_inicio: date, fecha_fin: date):
        if fecha_inicio >= fecha_fin:
            raise ValidationError("La fecha de inicio debe ser anterior a la fecha de fin.")
        if fecha_inicio < date.today():
            raise ValidationError("La fecha de inicio no puede ser en el pasado.")
        
        self._fecha_inicio = fecha_inicio
        self._fecha_fin = fecha_fin
        return self

    def add_herramienta(self, herramienta: Herramienta):
        if herramienta.estado != 'DISPONIBLE':
            raise ValidationError(f"La herramienta '{herramienta.nombre}' no está disponible.")
        if herramienta in self._herramientas:
            raise ValidationError(f"La herramienta '{herramienta.nombre}' ya está agregada a esta reserva.")
        
        self._herramientas.append(herramienta)
        return self

    def _calcular_costo_total(self) -> Decimal:
        dias = (self._fecha_fin - self._fecha_inicio).days
        costo_diario = sum(h.precio_por_dia for h in self._herramientas)
        return Decimal(dias) * costo_diario

    # ✔️ Sintaxis corregida aquí
    def build(self) -> Reserva:
        if not self._cliente:
            raise ValidationError("Falta asignar el cliente.")
        if not self._fecha_inicio or not self._fecha_fin:
            raise ValidationError("Falta asignar el rango de fechas.")
        if not self._herramientas:
            raise ValidationError("Debe incluir al menos una herramienta en la reserva.")

        costo_total = self._calcular_costo_total()

        # Creación de la instancia principal
        reserva = Reserva.objects.create(
            cliente=self._cliente,
            fecha_inicio=self._fecha_inicio,
            fecha_fin=self._fecha_fin,
            costo_total=costo_total,
            estado='PENDIENTE'
        )

        # Creación de los detalles asociados (relación M:N con captura de precio)
        for herramienta in self._herramientas:
            DetalleReserva.objects.create(
                reserva=reserva,
                herramienta=herramienta,
                precio_unitario_dia=herramienta.precio_por_dia
            )
            # Actualizar estado de la herramienta
            herramienta.estado = 'ALQUILADA'
            herramienta.save()

        return reserva
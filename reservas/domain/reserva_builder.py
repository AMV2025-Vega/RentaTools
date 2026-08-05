from reservas.models import Herramienta, Reserva

class ReservaBuilder:
    def __init__(self):
        self._herramienta_id = None
        self._usuario_id = None
        self._fecha_inicio = None
        self._fecha_fin = None

    def para_herramienta(self, herramienta_id):
        self._herramienta_id = herramienta_id
        return self

    def para_usuario(self, usuario_id):
        self._usuario_id = usuario_id
        return self

    def en_fechas(self, inicio, fin):
        self._fecha_inicio = inicio
        self._fecha_fin = fin
        return self

    def build(self):
        if (not self._herramienta_id or not self._usuario_id):
            raise ValueError("Herramienta y usuario son obligatorios")
        if (self._fecha_inicio >= self._fecha_fin):
            raise ValueError("Rango de fechas inválido")
        herramienta = Herramienta.objects.get(id=self._herramienta_id)
        if (not herramienta.verificar_disponibilidad(self._fecha_inicio, self._fecha_fin)):
            raise ValueError("Herramienta no disponible en esas fechas")
        return Reserva(
            herramienta_id=self._herramienta_id,
            usuario_id=self._usuario_id,
            fecha_inicio=self._fecha_inicio,
            fecha_fin=self._fecha_fin,
            estado="pendiente"
        )
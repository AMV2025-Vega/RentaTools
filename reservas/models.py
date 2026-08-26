from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Categoria(models.Model):
    """
    Representa las categorías de las herramientas (Ej: Construcción, Jardinería, Electricidad).
    """
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class Herramienta(models.Model):
    """
    Representa un item disponible para alquiler en la plataforma.
    """
    ESTADO_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('ALQUILADA', 'Alquilada'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
    ]

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    precio_por_dia = models.DecimalField(
        max_length=10, 
        decimal_places=2, 
        max_digits=10,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='DISPONIBLE')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='herramientas')
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.estado})"


class Cliente(models.Model):
    """
    Entidad que representa al cliente que realiza el alquiler.
    """
    nombre = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.email}"


class Reserva(models.Model):
    """
    Entidad principal que representa la transacción de alquiler de una o varias herramientas.
    """
    ESTADO_RESERVA = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
        ('FINALIZADA', 'Finalizada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='reservas')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    costo_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    estado = models.CharField(max_length=20, choices=ESTADO_RESERVA, default='PENDIENTE')
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reserva #{self.id} - Cliente: {self.cliente.nombre} - Estado: {self.estado}"


class DetalleReserva(models.Model):
    """
    Tabla intermedia para gestionar la relación M:N entre Reserva y Herramienta,
    registrando el precio capturado al momento del alquiler.
    """
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='detalles')
    herramienta = models.ForeignKey(Herramienta, on_delete=models.CASCADE, related_name='detalles')
    precio_unitario_dia = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle Reserva #{self.reserva.id} - {self.herramienta.nombre}"
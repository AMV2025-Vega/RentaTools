from django.db import models

class Herramienta(models.Model):
    nombre = models.CharField(max_length=100)

    def verificar_disponibilidad(self, inicio, fin):
        return True


class Reserva(models.Model):
    herramienta_id = models.IntegerField()
    usuario_id = models.IntegerField()

    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    estado = models.CharField(max_length=30)
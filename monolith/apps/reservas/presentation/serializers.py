from rest_framework import serializers


class CrearReservaInputSerializer(serializers.Serializer):
    """
    DTO de entrada. Valida SOLO forma y tipos (formato ISO de fecha, enteros).
    Las reglas (pasado, orden, disponibilidad) las aplica el dominio.
    """

    herramienta_id = serializers.IntegerField(min_value=1)
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()


class ReservaOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    cliente_id = serializers.IntegerField()
    herramienta_id = serializers.IntegerField()
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()
    dias = serializers.IntegerField()
    costo_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    moneda = serializers.CharField()
    estado = serializers.SerializerMethodField()
    creado_en = serializers.DateTimeField()

    def get_estado(self, obj) -> str:
        return obj.estado.value


class RangoOcupadoOutputSerializer(serializers.Serializer):
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()

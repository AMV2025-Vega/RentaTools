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


class CotizacionQuerySerializer(serializers.Serializer):
    """Parámetros de la URL (?herramienta_id=&fecha_inicio=&fecha_fin=): solo forma y tipos."""

    herramienta_id = serializers.IntegerField(min_value=1)
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()


class SeguroOutputSerializer(serializers.Serializer):
    aseguradora = serializers.CharField()
    prima = serializers.DecimalField(max_digits=14, decimal_places=2)
    cobertura_maxima = serializers.DecimalField(max_digits=14, decimal_places=2)
    moneda = serializers.CharField()


class CotizacionOutputSerializer(serializers.Serializer):
    herramienta_id = serializers.IntegerField()
    herramienta_nombre = serializers.CharField()
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()
    dias = serializers.IntegerField()
    costo_alquiler = serializers.DecimalField(max_digits=14, decimal_places=2)
    moneda = serializers.CharField()
    seguro = SeguroOutputSerializer(allow_null=True)
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_usd = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True)
    cop_por_usd = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True)
    tasa_actualizada_en = serializers.CharField(allow_null=True)
    avisos = serializers.ListField(child=serializers.CharField())
    # Términos de uso de la API gratuita de tasas: hay que mostrar este enlace junto a los valores en USD.
    atribucion = serializers.SerializerMethodField()

    def get_atribucion(self, obj):
        if obj.total_usd is None:
            return None
        return {"texto": "Rates By Exchange Rate API", "url": "https://www.exchangerate-api.com"}

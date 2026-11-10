from rest_framework import serializers


class CategoriaConteoSerializer(serializers.Serializer):
    categoria = serializers.CharField()
    herramientas = serializers.IntegerField()


class ResumenSerializer(serializers.Serializer):
    herramientas_activas = serializers.IntegerField()
    precio_promedio_dia = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    por_categoria = CategoriaConteoSerializer(many=True)
    reservas_total = serializers.IntegerField()
    reservas_por_estado = serializers.DictField(child=serializers.IntegerField())


class EstadisticasOutputSerializer(serializers.Serializer):
    sistema = serializers.CharField()
    version = serializers.CharField()
    generado_en = serializers.DateTimeField()
    moneda = serializers.CharField()
    resumen = ResumenSerializer()

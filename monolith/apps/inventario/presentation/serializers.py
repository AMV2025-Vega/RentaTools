from rest_framework import serializers


class CategoriaOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    descripcion = serializers.CharField()


class PublicarHerramientaInputSerializer(serializers.Serializer):
    categoria_id = serializers.IntegerField()
    nombre = serializers.CharField(max_length=150)
    descripcion = serializers.CharField(required=False, allow_blank=True, default="")
    precio_por_dia = serializers.DecimalField(max_digits=10, decimal_places=2)
    foto_url = serializers.URLField(required=False, allow_blank=True, default="")


class CambiarEstadoInputSerializer(serializers.Serializer):
    estado = serializers.CharField()


class HerramientaOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    propietario_id = serializers.IntegerField()
    categoria_id = serializers.IntegerField()
    categoria_nombre = serializers.CharField()
    nombre = serializers.CharField()
    descripcion = serializers.CharField()
    precio_por_dia = serializers.DecimalField(max_digits=10, decimal_places=2)
    estado = serializers.SerializerMethodField()
    foto_url = serializers.CharField()

    def get_estado(self, obj) -> str:
        return obj.estado.value

from rest_framework import serializers
from reservas.models import Herramienta, Cliente, Reserva, Categoria


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion']


class HerramientaSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)

    class Meta:
        model = Herramienta
        fields = ['id', 'nombre', 'descripcion', 'precio_por_dia', 'estado', 'categoria']


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'email', 'telefono', 'direccion']


class CrearReservaInputSerializer(serializers.Serializer):
    """
    Serializer de entrada (DTO) para la creación de una reserva.
    No ejecuta lógica de negocio, solo valida tipos de datos del request.
    """
    cliente_id = serializers.IntegerField()
    herramientas_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()
    tipo_notificacion = serializers.ChoiceField(
        choices=['EMAIL', 'SMS'], default='EMAIL', required=False
    )


class ReservaOutputSerializer(serializers.ModelSerializer):
    """
    Serializer de salida para presentar la reserva al cliente/frontend.
    """
    cliente = ClienteSerializer(read_only=True)
    
    class Meta:
        model = Reserva
        fields = ['id', 'cliente', 'fecha_inicio', 'fecha_fin', 'costo_total', 'estado', 'creado_en']
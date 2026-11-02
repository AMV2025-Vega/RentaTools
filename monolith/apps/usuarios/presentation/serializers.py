from rest_framework import serializers


class RegistroInputSerializer(serializers.Serializer):
    """DTO de entrada: valida solo forma y tipos; las reglas viven en el servicio."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")


class LoginInputSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)


class UsuarioOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    telefono = serializers.CharField()

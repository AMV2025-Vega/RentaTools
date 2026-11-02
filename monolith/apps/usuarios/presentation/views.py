from django.contrib.auth import authenticate, login, logout
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.compartido.excepciones import DominioError
from apps.compartido.presentacion import respuesta_de_error
from apps.usuarios.composition import construir_registro_service
from apps.usuarios.domain.entities import UsuarioDTO
from apps.usuarios.presentation.serializers import (
    LoginInputSerializer,
    RegistroInputSerializer,
    UsuarioOutputSerializer,
)


class RegistroAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []  # registro público, sin CSRF de sesión

    def post(self, request):
        entrada = RegistroInputSerializer(data=request.data)
        if not entrada.is_valid():
            return Response(entrada.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            usuario = construir_registro_service().registrar(**entrada.validated_data)
        except DominioError as exc:
            return respuesta_de_error(exc)
        return Response(UsuarioOutputSerializer(usuario).data, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    """Inicia sesión (cookie de sesión de Django). Manejo de sesión = framework, no negocio."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        entrada = LoginInputSerializer(data=request.data)
        if not entrada.is_valid():
            return Response(entrada.errors, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, **entrada.validated_data)
        if user is None:
            return Response({"codigo": "credenciales_invalidas", "error": "Credenciales inválidas."}, status=status.HTTP_400_BAD_REQUEST)
        login(request, user)
        dto = UsuarioDTO(user.id, user.username, user.email, user.telefono)
        return Response(UsuarioOutputSerializer(dto).data, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PerfilAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        dto = UsuarioDTO(u.id, u.username, u.email, u.telefono)
        return Response(UsuarioOutputSerializer(dto).data)

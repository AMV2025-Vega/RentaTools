"""
Vistas delgadas: validan el contrato (serializer), delegan en el servicio y
traducen el resultado/errores a HTTP. Cero lógica de negocio aquí.

Códigos: 201 creada · 200 ok · 400 datos/regla inválida · 403 sin permiso ·
404 no existe · 409 conflicto (fechas ocupadas / estado inválido).
"""
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.compartido.excepciones import DominioError
from apps.compartido.presentacion import respuesta_de_error, solicitante_desde
from apps.reservas.composition import construir_cotizacion_service, construir_reserva_service
from apps.reservas.presentation.serializers import (
    CotizacionOutputSerializer,
    CotizacionQuerySerializer,
    CrearReservaInputSerializer,
    RangoOcupadoOutputSerializer,
    ReservaOutputSerializer,
)


class ReservasAPIView(APIView):
    def get(self, request):
        reservas = construir_reserva_service().listar_mis_reservas(solicitante_desde(request))
        return Response(ReservaOutputSerializer(reservas, many=True).data)

    def post(self, request):
        entrada = CrearReservaInputSerializer(data=request.data)
        if not entrada.is_valid():
            return Response(entrada.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            reserva = construir_reserva_service().crear_reserva(solicitante_desde(request), **entrada.validated_data)
        except DominioError as exc:
            return respuesta_de_error(exc)
        return Response(ReservaOutputSerializer(reserva).data, status=status.HTTP_201_CREATED)


class ReservaCancelarAPIView(APIView):
    def post(self, request, pk):
        try:
            reserva = construir_reserva_service().cancelar_reserva(solicitante_desde(request), pk)
        except DominioError as exc:
            return respuesta_de_error(exc)
        return Response(ReservaOutputSerializer(reserva).data, status=status.HTTP_200_OK)


class OcupacionHerramientaAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            rangos = construir_reserva_service().ocupacion(pk)
        except DominioError as exc:
            return respuesta_de_error(exc)
        return Response(RangoOcupadoOutputSerializer(rangos, many=True).data)


class CotizacionAPIView(APIView):
    """Cotización pública (sin reservar): costo + seguro del aliado + total en USD (tercero)."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request):
        entrada = CotizacionQuerySerializer(data=request.query_params)
        if not entrada.is_valid():
            return Response(entrada.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            cotizacion = construir_cotizacion_service().cotizar(**entrada.validated_data)
        except DominioError as exc:
            return respuesta_de_error(exc)
        return Response(CotizacionOutputSerializer(cotizacion).data)

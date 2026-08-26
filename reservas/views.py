from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from reservas.services import ReservaService, HerramientaService
from reservas.serializers import (
    CrearReservaInputSerializer, 
    ReservaOutputSerializer, 
    HerramientaSerializer
)


class HerramientasDisponiblesAPIView(APIView):
    """
    APIView para consultar el catálogo de herramientas disponibles.
    """
    def get(self, request):
        herramientas = HerramientaService.listar_disponibles()
        serializer = HerramientaSerializer(herramientas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReservaCrearAPIView(APIView):
    """
    APIView para orquestar la creación de una reserva.
    Manaje explícitamente los códigos de estado HTTP (201, 400, 404, 409).
    """
    def post(self, request):
        # 1. Validación de contrato sintáctico con el Serializer
        serializer = CrearReservaInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Delegación limpia a la Capa de Servicios
        try:
            reserva = ReservaService.crear_reserva(
                cliente_id=serializer.validated_data['cliente_id'],
                herramientas_ids=serializer.validated_data['herramientas_ids'],
                fecha_inicio=serializer.validated_data['fecha_inicio'],
                fecha_fin=serializer.validated_data['fecha_fin'],
                tipo_notificacion=serializer.validated_data.get('tipo_notificacion', 'EMAIL')
            )
            output_serializer = ReservaOutputSerializer(reserva)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except ObjectDoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValidationError as e:
            # Errores de regla de negocio/conflicto (disponibilidad, fechas inválidas)
            return Response({"error": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_409_CONFLICT)

        except Exception as e:
            return Response({"error": "Error interno del servidor.", "detalle": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReservaCancelarAPIView(APIView):
    """
    APIView para cancelar una reserva existente.
    """
    def post(self, request, pk):
        try:
            reserva = ReservaService.cancelar_reserva(reserva_id=pk)
            output_serializer = ReservaOutputSerializer(reserva)
            return Response(output_serializer.data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except ValidationError as e:
            return Response({"error": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_409_CONFLICT)
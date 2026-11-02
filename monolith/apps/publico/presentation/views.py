from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.publico.composition import construir_estadisticas_service
from apps.publico.presentation.serializers import EstadisticasOutputSerializer


class EstadisticasPublicasAPIView(APIView):
    """GET /api/publico/estadisticas/ -> JSON público de solo lectura."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request):
        return Response(EstadisticasOutputSerializer(construir_estadisticas_service().obtener()).data)

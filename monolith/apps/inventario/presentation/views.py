from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.compartido.excepciones import DominioError
from apps.compartido.presentacion import respuesta_de_error
from apps.inventario.composition import construir_herramienta_service
from apps.inventario.presentation.serializers import (
    CambiarEstadoInputSerializer,
    CategoriaOutputSerializer,
    HerramientaOutputSerializer,
    PublicarHerramientaInputSerializer,
)


class CategoriasAPIView(APIView):
    permission_classes = [AllowAny]  # el catálogo es público

    def get(self, request):
        categorias = construir_herramienta_service().listar_categorias()
        return Response(CategoriaOutputSerializer(categorias, many=True).data)


class HerramientasAPIView(APIView):
    """GET: catálogo (público, filtros ?categoria_id= & ?mias=1). POST: publicar (autenticado)."""

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsAuthenticated()]

    def get(self, request):
        categoria_id = request.query_params.get("categoria_id")
        propietario_id = request.user.id if request.query_params.get("mias") and request.user.is_authenticated else None
        herramientas = construir_herramienta_service().listar(
            categoria_id=int(categoria_id) if categoria_id and categoria_id.isdigit() else None,
            propietario_id=propietario_id,
            solo_activas=propietario_id is None,  # el dueño ve también las que tiene en mantenimiento
        )
        return Response(HerramientaOutputSerializer(herramientas, many=True).data)

    def post(self, request):
        entrada = PublicarHerramientaInputSerializer(data=request.data)
        if not entrada.is_valid():
            return Response(entrada.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            herramienta = construir_herramienta_service().publicar(propietario_id=request.user.id, **entrada.validated_data)
        except DominioError as exc:
            return respuesta_de_error(exc)
        return Response(HerramientaOutputSerializer(herramienta).data, status=status.HTTP_201_CREATED)


class HerramientaDetalleAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            herramienta = construir_herramienta_service().obtener(pk)
        except DominioError as exc:
            return respuesta_de_error(exc)
        return Response(HerramientaOutputSerializer(herramienta).data)


class HerramientaEstadoAPIView(APIView):
    def patch(self, request, pk):
        entrada = CambiarEstadoInputSerializer(data=request.data)
        if not entrada.is_valid():
            return Response(entrada.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            herramienta = construir_herramienta_service().cambiar_estado(request.user.id, pk, entrada.validated_data["estado"])
        except DominioError as exc:
            return respuesta_de_error(exc)
        return Response(HerramientaOutputSerializer(herramienta).data)

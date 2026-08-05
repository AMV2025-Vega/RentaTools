from django.views import View
from django.http import JsonResponse

from .services import ReservaService

class CrearReservaView(View):
    def post(self, request):
        datos = request.POST
        servicio = ReservaService()
        reserva = servicio.crear_reserva(datos)
        return JsonResponse({"id": reserva.id, "estado": reserva.estado})
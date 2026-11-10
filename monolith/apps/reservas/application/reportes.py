"""
Reportes en segundo plano. El servicio solo conoce el puerto `ColaReportes`:
no sabe que detrás hay Celery + Redis (DIP).
"""
import csv
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass

from apps.compartido.excepciones import Prohibido
from apps.compartido.puertos import Solicitante
from apps.reservas.application.ports import ReservaRepository

ENCABEZADOS = ["id", "herramienta_id", "fecha_inicio", "fecha_fin", "dias", "costo_total", "moneda", "estado", "creado_en"]


@dataclass(frozen=True)
class EstadoTarea:
    id: str
    estado: str  # PENDIENTE | EN_CURSO | LISTO | FALLIDO
    resultado: dict | None = None


class ColaReportes(ABC):
    @abstractmethod
    def solicitar_reporte_reservas(self, cliente_id: int) -> str:
        """Encola la generación y devuelve el id de la tarea. Lanza ServicioNoDisponible si no hay cola."""

    @abstractmethod
    def consultar(self, tarea_id: str) -> EstadoTarea: ...


class ReporteService:
    def __init__(self, repo: ReservaRepository, cola: ColaReportes):
        self._repo = repo
        self._cola = cola

    def solicitar(self, solicitante: Solicitante) -> str:
        return self._cola.solicitar_reporte_reservas(solicitante.id)

    def consultar(self, solicitante: Solicitante, tarea_id: str) -> EstadoTarea:
        estado = self._cola.consultar(tarea_id)
        # El resultado trae el dueño: nadie descarga el reporte de otro usuario.
        if estado.resultado and estado.resultado.get("cliente_id") != solicitante.id:
            raise Prohibido("Ese reporte pertenece a otro usuario.", "reporte_ajeno")
        return estado

    def generar_csv(self, cliente_id: int) -> dict:
        """Lo ejecuta el worker."""
        reservas = self._repo.listar_por_cliente(cliente_id)
        salida = io.StringIO()
        escritor = csv.writer(salida)
        escritor.writerow(ENCABEZADOS)
        for r in reservas:
            escritor.writerow(
                [r.id, r.herramienta_id, r.fecha_inicio, r.fecha_fin, r.dias, r.costo_total, r.moneda, r.estado.value,
                 r.creado_en.isoformat() if r.creado_en else ""]
            )
        return {"cliente_id": cliente_id, "nombre_archivo": "mis-reservas.csv", "contenido": salida.getvalue(), "filas": len(reservas)}

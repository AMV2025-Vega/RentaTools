# Sprint 3 — Procesos de fondo con Celery + Redis (2-nov-2026)

## Objetivo
Cumplir "comunicación asíncrona con Message Broker (Redis/Celery) para procesos de fondo (reportes, notificaciones)".

## Entregado
- `redis` (solo `data_net`) y `worker` (misma imagen de Django) en Docker Compose; el `entrypoint.sh` ejecuta el comando que reciba (worker) sin migrar.
- **Notificaciones asíncronas** con reintentos (backoff exponencial, máx. 3) y `NotificadorAsincrono` (Decorator) sobre la Factory.
- **Reportes CSV** en segundo plano: `POST /api/reportes/reservas/` → `202`, `GET /api/reportes/<id>/` (polling), con control de propietario.
- El puerto `Notificador` ahora recibe *plantilla + contexto + idioma* (no texto): base de la i18n del Sprint 4.
- `ServicioNoDisponible` → HTTP `503` si el broker no responde.
- 70 pruebas del monolito; verificado con Redis y worker reales.

## Decisiones
| Decisión | Motivo |
|---|---|
| Notificar tras el commit y de forma asíncrona | Una reserva confirmada no depende de que el correo salga; la petición responde en ~100 ms |
| Redis efímero (sin persistencia) | Las tareas son reintentables y de baja criticidad; simplifica el despliegue en una sola EC2 |
| Plantilla + contexto en la tarea | JSON serializable, traducible en el worker y sin textos quemados en la lógica |
| Resultado con `cliente_id` y chequeo en el servicio | Evita que un `tarea_id` adivinado exponga datos de otro usuario |

## Pendiente
Frontend + i18n (Sprint 4) · despliegue en AWS (Sprint 5).

# Sprint 1 — Base arquitectónica y flujo de reservas (31-oct-2026)

## Objetivo
Reiniciar la base del Taller 1 con una arquitectura defendible (SOLID, capas, Docker) y dejar el flujo
Usuario → Herramienta → Reserva funcionando de punta a punta.

## Entregado
- Monolito Django modular: `usuarios`, `inventario`, `reservas`, `auditoria` (+ `compartido`).
- Builder (Reserva), Factory (Notificador), Adapter (Costo), Service Layer inyectable.
- API: registro/login, categorías, herramientas (publicar, listar, estado), reservas (crear, listar, cancelar), ocupación.
- Anti doble reserva en PostgreSQL (ExclusionConstraint) + auditoría inmutable.
- Microservicio Flask de costos (Strangler) con respaldo local en el monolito.
- Docker Compose (Alpine, 3 capas con redes aisladas) + Nginx gateway.
- 45 pruebas del monolito + 9 del microservicio.

## Decisiones (y por qué)
| Decisión | Motivo |
|---|---|
| Reiniciar la base | El Taller 1 mezclaba persistencia en el Builder, estado global de disponibilidad y servicios estáticos |
| 1 reserva = 1 herramienta | Coherente con el diagrama de clases; un propietario, un pago, un depósito |
| Disponibilidad por fechas, no por `estado` | Una herramienta puede estar reservada en noviembre y libre hoy |
| Días inclusivos (inicio y fin cuentan) | Regla ya implementada por el microservicio de costos |
| Frontend con plantillas Django | i18n con gettext nativo, un contenedor menos, plazo de 3 días |

## Pendiente (siguientes sprints)
Pago/Depósito/Reseña como microservicio · frontend + i18n · Redis/Celery · API de terceros y servicio del aliado · despliegue AWS.

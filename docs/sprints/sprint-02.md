# Sprint 2 — Integraciones: aliado, tercero y servicio propio (1-nov-2026)

## Objetivo
Cubrir el bloque "Servicios" de la Entrega 2 (30 %): proveer un JSON, consumir al aliado y consumir un tercero vía Adapter.

## Entregado
- **Servicio aliado simulado** (`services/aliado`, Flask): cotizador de seguros con API key, validaciones y contrato en `docs/contrato-aliado.md`.
- **Adapter del aliado** y **Adapter de tasas de cambio** (API de terceros) con caché y respaldo (Decorator).
- **Cotización** (`GET /api/cotizaciones/`): costo + seguro + USD, con degradación elegante si falla un externo.
- **Servicio a proveer** (`GET /api/publico/estadisticas/`).
- Regla de fechas extraída a `domain/reglas.py` (la usan Builder y cotización: una sola fuente de verdad).
- Compose con el servicio `aliado` en `edge_net`, sin puerto publicado.
- 60 pruebas del monolito · 12 del aliado · 9 de costos.

## Decisiones
| Decisión | Motivo |
|---|---|
| Aliado = seguros | Servicio natural para un alquiler y no exige cambiar el modelo de datos |
| Montos como string en el contrato | Evita errores de precisión de `float` |
| Fallo externo ⇒ aviso, no error | Un tercero caído no debe tumbar la cotización ni la reserva |
| Aliado fuera de Nginx | Mantiene a Nginx como única puerta de entrada pública |
| Cache de tasas 6 h + última conocida | La API gratuita actualiza 1 vez/día y responde 429 si se abusa |

## Pendiente
Frontend con i18n (mostrar cotización, seguro y USD con la atribución) · Pago/Depósito en Flask · Redis/Celery · AWS.

# Contrato de integración con el servicio ALIADO

> **AseguraTools (simulado)** — cotizador de seguros de alquiler. Representa al servicio del equipo aliado.
> RentaTools solo conoce este contrato; si el aliado real cambia su implementación, solo se reescribe
> `monolith/apps/reservas/infrastructure/aliado_seguros.py` (Adapter).

| | |
|---|---|
| **URL base (red interna Docker)** | `http://aliado:5001/api/v1` |
| **URL base (pruebas locales fuera de Docker)** | `http://127.0.0.1:5001/api/v1` |
| **Autenticación** | Cabecera `X-API-Key: <clave>` (variable `ALIADO_API_KEY`). Sin clave o con clave errónea → `401` |
| **Formato** | JSON UTF-8, `Content-Type: application/json` |
| **Montos** | Cadenas decimales (`"36000.00"`), nunca `float`, para no perder precisión |
| **Timeout del cliente** | 3 s. Si falla, RentaTools sigue cotizando **sin seguro** y devuelve `avisos: ["seguro_no_disponible"]` |
| **Exposición** | No se publica en Nginx ni en el Security Group: solo Django lo alcanza por `edge_net` |

## `POST /api/v1/seguros/cotizar`

### Petición
```json
{ "valor_alquiler": "36000.00", "dias": 3, "categoria": "Construcción", "moneda": "COP" }
```
| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `valor_alquiler` | string/número decimal | sí | > 0 |
| `dias` | entero | sí | 1 … 30 |
| `categoria` | string | no | Define la tasa; desconocida/vacía → tasa por defecto |
| `moneda` | string | no | Solo `"COP"` |

### Respuesta `200`
```json
{
  "aseguradora": "AseguraTools S.A.S. (simulada)",
  "prima": "3660.00",
  "cobertura_maxima": "720000.00",
  "moneda": "COP",
  "tasa_aplicada": "0.06"
}
```
**Regla de negocio simulada:** `prima = max(2000, valor × tasa) + 500 × días`; `cobertura_maxima = max(valor × 20, 200000)`.
Tasas: Construcción 6 % · Jardinería 5 % · Electricidad 7 % · Carpintería 4 % · Limpieza 3 % · otras 5 %.

### Errores
| Código | Cuerpo | Cuándo |
|---|---|---|
| `400` | `{"error": "solicitud_invalida", "message": "..."}` | Campos ausentes o inválidos |
| `401` | `{"error": "no_autorizado", "message": "..."}` | API key ausente/errónea |
| `404` / `405` / `500` | `{"error": "...", "message": "..."}` | Ruta/método inexistente o fallo interno |

### Ejemplo
```powershell
curl.exe -X POST http://127.0.0.1:5001/api/v1/seguros/cotizar -H "Content-Type: application/json" -H "X-API-Key: TU_CLAVE" -d '{\"valor_alquiler\":36000,\"dias\":3,\"categoria\":\"Construcción\"}'
```

### Salud
`GET /health` → `{"estado":"ok","servicio":"aliado-seguros"}` (sin API key; lo usa Docker).

---

# Servicios que RentaTools expone

## `GET /api/cotizaciones/?herramienta_id=&fecha_inicio=&fecha_fin=` (público)
Combina **costo** (microservicio Flask) + **seguro** (aliado, Adapter) + **total en USD** (API de terceros, Adapter).
```json
{
  "herramienta_id": 1, "herramienta_nombre": "Taladro",
  "fecha_inicio": "2026-11-05", "fecha_fin": "2026-11-07", "dias": 3,
  "costo_alquiler": "36000.00", "moneda": "COP",
  "seguro": { "aseguradora": "AseguraTools S.A.S. (simulada)", "prima": "3660.00", "cobertura_maxima": "720000.00", "moneda": "COP" },
  "total": "39660.00", "total_usd": "9.92", "cop_por_usd": "4000.00",
  "tasa_actualizada_en": "Sat, 31 Oct 2026 00:00:01 +0000",
  "avisos": [],
  "atribucion": { "texto": "Rates By Exchange Rate API", "url": "https://www.exchangerate-api.com" }
}
```
`avisos` puede contener `seguro_no_disponible` y/o `conversion_no_disponible` (degradación elegante: nunca un 500 por un tercero caído).
Errores: `400` (fechas inválidas/pasadas), `404` (herramienta inexistente).

## `GET /api/publico/estadisticas/` (público, solo lectura, sin datos personales)
```json
{
  "sistema": "RentaTools", "version": "1.0", "generado_en": "2026-11-01T10:00:00-05:00", "moneda": "COP",
  "resumen": {
    "herramientas_activas": 12, "precio_promedio_dia": "15000.00",
    "por_categoria": [ { "categoria": "Construcción", "herramientas": 5 } ],
    "reservas_total": 8,
    "reservas_por_estado": { "PENDIENTE_PAGO": 3, "CONFIRMADA": 2, "CANCELADA": 2, "FINALIZADA": 1 }
  }
}
```

# API de terceros: tasas de cambio
[ExchangeRate-API — acceso abierto](https://www.exchangerate-api.com/docs/free): `GET https://open.er-api.com/v6/latest/COP`, sin llave.
Se actualiza una vez al día y limita peticiones (HTTP 429), por eso `ConversorConCache` guarda la tasa 6 h y, si la API falla,
reutiliza la última conocida. **Condición de uso:** mostrar el enlace "Rates By Exchange Rate API" junto a los valores en USD
(el campo `atribucion` ya lo trae para el frontend).

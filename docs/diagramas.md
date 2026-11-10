# Diagramas de arquitectura (Entrega 2)

## 1. Infraestructura AWS
```mermaid
flowchart TB
    U([Usuario / navegador]) -- "HTTP :80" --> EIP[Elastic IP]
    subgraph AWS [AWS · región a elección]
      subgraph SG [Security Group · entrada: 80 público, 22 solo IP admin]
        subgraph EC2 [EC2 · Amazon Linux 2023 · Docker Engine + Compose]
          direction TB
          subgraph edge [edge_net]
            NG[nginx:alpine<br/>API Gateway]
            DJ[django + gunicorn]
            CO[flask: costos]
            AL[flask: aliado seguros]
            WK[celery worker]
          end
          subgraph data [data_net · internal]
            PG[(PostgreSQL 16)]
            RD[(Redis · broker)]
          end
        end
      end
    end
    EIP --> NG
    ADM([Administrador]) -. "SSH :22 (IP restringida)" .-> EC2
    DJ -. "HTTPS saliente" .-> EXT([ExchangeRate-API])
```

## 2. Nginx como API Gateway (Strangler Fig)
```mermaid
flowchart LR
    C([Cliente]) --> N{{nginx :80<br/>rate limit · X-Request-ID}}
    N -- "/static/*" --> S[(volumen static_data<br/>servido directo)]
    N -- "/api/v2/reservas/costo/" --> F[Flask · costos<br/>microservicio extraído]
    N -- "/ (todo lo demás)" --> M[Django · monolito]
    M -. "mientras se estabiliza" .-> F
```
Cuando otro módulo se extraiga, basta agregar un `location` nuevo: el cliente no cambia.

## 3. Servicios Flask (microservicios)
```mermaid
flowchart LR
    subgraph costo [Servicio de costos]
      R1[routes.py<br/>HTTP] --> S1[services.py<br/>reglas de cálculo]
    end
    subgraph aliado [Servicio ALIADO · seguros simulado]
      R2[POST /api/v1/seguros/cotizar<br/>X-API-Key] --> S2[prima = max&#40;2000, valor×tasa&#41; + 500×días]
    end
    M[Monolito Django] -- "Adapter CostoHttp" --> R1
    M -- "Adapter AliadoSeguros<br/>JSON + API key" --> R2
```

## 4. Message broker (Redis + Celery)
```mermaid
sequenceDiagram
    participant U as Usuario
    participant D as Django
    participant R as Redis (broker)
    participant W as Worker Celery
    participant P as PostgreSQL
    U->>D: POST /api/reservas/
    D->>P: guarda reserva + auditoría (transacción)
    D-->>R: encola enviar_notificacion (tras commit)
    D-->>U: 201 Created (sin esperar el correo)
    R->>W: entrega tarea
    W->>W: envía en el idioma del usuario (reintentos, backoff)
    U->>D: POST /api/reportes/reservas/
    D-->>R: encola generar_reporte_reservas
    D-->>U: 202 + tarea_id
    W->>P: consulta reservas
    U->>D: GET /api/reportes/{id}/ (polling) → LISTO + CSV
```

## 5. Flujo de servicios (rúbrica)
| Requisito | Dónde |
|---|---|
| Proveer endpoint JSON | `/api/...` del monolito y `/api/v2/reservas/costo/` (Flask) |
| Consumir servicio del aliado | `aliado_seguros.py` → servicio `aliado` |
| API de tercero con Adapter | `tasas_cambio.py` (ExchangeRate-API, caché y respaldo) |

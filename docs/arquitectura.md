# Arquitectura de RentaTools

## 1. Vista de despliegue y redes (3 capas aisladas)

```mermaid
flowchart LR
    U([Internet]) -- ":80" --> N[nginx<br/>API Gateway]
    subgraph edge_net [edge_net · presentación]
        N --> D[django + gunicorn<br/>monolito modular]
        N -- "/api/v2/reservas/costo/" --> C[flask + gunicorn<br/>servicio de costos]
        D -- "HTTP (Adapter)" --> C
    end
    subgraph data_net [data_net · interna, sin salida a Internet]
        D --> P[(PostgreSQL 16)]
    end
```

* Solo `nginx` publica un puerto (80). `db` y `costo` no son alcanzables desde fuera.
* `data_net` es `internal: true`: PostgreSQL no tiene ruta hacia Internet.
* Security Group en AWS: entrada TCP 80 pública; SSH (22) solo desde la IP del administrador.

## 2. Estructura interna de cada módulo (Clean/Hexagonal ligera)

```
apps/<modulo>/
  domain/           reglas de negocio puras (entidades, Builder). Sin Django.
  application/      servicios (casos de uso) + puertos (interfaces ABC). Sin Django.
  infrastructure/   adaptadores: repositorios ORM, cliente HTTP, Factory de notificadores.
  presentation/     serializers (solo forma/tipos) + APIView (solo HTTP).
  composition.py    único lugar que decide qué implementación concreta se inyecta.
  models.py         persistencia "delgada": campos y constraints de BD.
```

Regla de dependencias: `presentation → application → domain` y `infrastructure → application/domain`.
El dominio y la aplicación **nunca** importan Django.

### SOLID, dónde se ve

| Principio | Evidencia |
|---|---|
| **S**RP | View = HTTP · Serializer = forma · Service = orquestación · Builder = construir/validar · Repository = persistir · Calculadora = costo |
| **O**CP | `NotificadorFactory.registrar()` añade canales sin tocar código existente |
| **L**SP | `CostoHttpAdapter`, `CalculadoraLocal` y `CalculadoraConRespaldo` son intercambiables vía `CalculadoraCosto` |
| **I**SP | Puertos pequeños y específicos (`Notificador`, `CatalogoHerramientas`, `AuditLogger`…) |
| **D**IP | `ReservaService` recibe 7 abstracciones por constructor; las concretas se eligen en `composition.py` |

### Patrones
* **Builder** (`reservas/domain/reserva_builder.py`): construye y valida la `Reserva`, la entidad más compleja.
* **Factory** (`reservas/infrastructure/notificadores.py`): elige el notificador según `ENV_TYPE`.
* **Adapter** (`reservas/infrastructure/costo.py`): traduce el puerto `CalculadoraCosto` al contrato HTTP del microservicio.
* **Strangler Fig**: el cálculo de costo salió del monolito; Nginx enruta `/api/v2/reservas/costo/` al servicio Flask y el monolito conserva un respaldo local mientras se estabiliza.

## 3. Caso más complejo: crear una reserva

```mermaid
sequenceDiagram
    actor C as Cliente
    participant N as Nginx
    participant V as ReservasAPIView
    participant S as ReservaService
    participant B as ReservaBuilder
    participant K as CalculadoraCosto (Adapter)
    participant F as Flask costo
    participant R as ReservaRepository
    participant DB as PostgreSQL
    participant A as AuditLogger
    C->>N: POST /api/reservas/
    N->>V: proxy (X-Request-ID)
    V->>V: Serializer valida forma
    V->>S: crear_reserva(solicitante, herramienta, fechas)
    S->>B: con_cliente / con_herramienta / con_fechas / build
    B-->>S: ReservaNueva (reglas validadas)
    S->>K: calcular(...)
    K->>F: POST /api/v2/reservas/costo/
    F-->>K: dias, total (o falla → cálculo local)
    S->>R: crear(nueva, costo)  [transacción]
    R->>DB: INSERT (ExclusionConstraint evita solapes)
    DB-->>R: ok / violación → ConflictoDisponibilidad
    S->>A: RESERVA_CREADA (misma transacción)
    S-->>V: Reserva
    V-->>C: 201 (o 400 / 404 / 409)
    Note over S: tras el commit: notificación (best effort)
```

### Doble reserva: garantizada por la base de datos
`ExclusionConstraint(daterange(inicio, fin, '[]') && , herramienta =)` sobre reservas vigentes. Con dos
peticiones simultáneas PostgreSQL deja pasar una; la otra recibe `409 herramienta_no_disponible`
(verificado con una prueba de concurrencia real).

### Auditoría
Cada transacción relevante escribe un `RegistroAuditoria` (BD) + una línea JSON en stdout. Los rechazos
(400/404/409) también se auditan (`resultado=RECHAZADO`). La tabla es **inmutable** por un trigger de PostgreSQL.

## 4. Visión de API Gateway y escalabilidad
Nginx ya es el gateway: toda ruta pasa por él, aplica límites de tasa, cabeceras de seguridad y añade
`X-Request-ID`. Extraer otro módulo (p. ej. Pagos) = nuevo contenedor + un `location` en `nginx.conf`
+ reemplazar su adaptador en `composition.py`; los demás módulos no cambian.

# RentaTools

Marketplace de alquiler de herramientas entre particulares. Proyecto del curso Arquitectura de Software 2026.

**Stack:** Django + DRF (monolito modular) · Flask (microservicio de costos) · PostgreSQL 16 · Nginx (API Gateway) · Gunicorn · Docker Compose (imágenes Alpine) · AWS EC2.

## Arrancar en local (Windows, VS Code)

```powershell
Copy-Item .env.example .env        # y edite las claves
docker compose up -d --build
curl.exe http://localhost/api/salud/
docker compose exec django python manage.py createsuperuser   # opcional, para /admin/
```

Pruebas:

```powershell
docker compose exec django python manage.py test apps          # monolito (60 pruebas)
cd services\costo; pip install -r requirements.txt pytest; python -m pytest -q   # microservicio
```

## Estructura

```
gateway/            Nginx: única puerta de entrada (puerto 80)
monolith/           Django. apps/<modulo>/{domain,application,infrastructure,presentation}
services/costo/     Microservicio Flask extraído del monolito (Strangler)
services/aliado/    Servicio del aliado (seguros), simulado, solo interno
docs/               Arquitectura, contrato del aliado y bitácora de sprints (base de la Wiki)
```

Más detalle en [`docs/arquitectura.md`](docs/arquitectura.md).

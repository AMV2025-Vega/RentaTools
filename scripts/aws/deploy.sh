#!/usr/bin/env bash
# Despliega (o actualiza) RentaTools en la EC2. Ejecutar desde la raíz del repo clonado.
#   1ª vez:  cp .env.example .env && nano .env   (claves, ALLOWED_HOSTS con la IP elástica)
#   siempre: bash scripts/aws/deploy.sh
set -euo pipefail
cd "$(dirname "$0")/../.."

[ -f .env ] || { echo "Falta .env: copia .env.example y edítalo (ver docs/despliegue-aws.md)"; exit 1; }
grep -q "cambia-" .env && { echo "Aún hay valores 'cambia-...' en .env: reemplázalos antes de desplegar"; exit 1; }

git pull --ff-only || echo "(sin git pull: se usa el código local)"
docker compose up -d --build
echo "Esperando a que todos los servicios estén saludables..."
for i in $(seq 1 40); do
  pendientes=$(docker compose ps --format '{{.Name}} {{.Health}}' | grep -vc "healthy$" || true)
  # nginx/worker pueden no tener healthcheck; basta con que la API responda.
  if curl -fsS http://localhost/api/salud/ >/dev/null 2>&1; then break; fi
  sleep 5
done
bash scripts/aws/smoke-test.sh http://localhost

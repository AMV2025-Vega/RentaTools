#!/usr/bin/env bash
# Prueba de humo contra una URL base (por defecto, local). Sirve también desde tu PC contra la IP pública:
#   bash scripts/aws/smoke-test.sh http://<IP-ELASTICA>
BASE="${1:-http://localhost}"
fallos=0
chequea() {  # descripción, comando
  if eval "$2" >/dev/null 2>&1; then echo "  OK   $1"; else echo "  FALLA $1"; fallos=$((fallos+1)); fi
}
echo "Smoke test → $BASE"
chequea "Gateway + monolito (/api/salud/)"            "curl -fsS $BASE/api/salud/"
chequea "Frontend (catálogo)"                         "curl -fsS $BASE/ | grep -q RentaTools"
chequea "Estáticos servidos por Nginx"                "curl -fsS $BASE/static/web/css/app.css"
chequea "API pública (estadísticas)"                  "curl -fsS $BASE/api/publico/estadisticas/"
chequea "Microservicio de costos vía Nginx (Strangler)" "curl -fsS -X POST $BASE/api/v2/reservas/costo/ -H 'Content-Type: application/json' -d '{\"fecha_inicio\":\"2026-12-01\",\"fecha_fin\":\"2026-12-03\",\"herramientas\":[{\"precio_por_dia\":1000}]}'"
chequea "i18n: inglés disponible"                     "curl -fsS -H 'Accept-Language: en' $BASE/ | grep -q 'Skip to content'"
chequea "Aliado NO expuesto (debe rechazar)"          "! curl -fsS --max-time 3 $BASE:5001/"
chequea "Postgres NO expuesto"                        "! (echo > /dev/tcp/${BASE#http://}/5432) 2>/dev/null"
[ "$fallos" -eq 0 ] && echo "Todo bien." || { echo "$fallos comprobación(es) fallaron."; exit 1; }

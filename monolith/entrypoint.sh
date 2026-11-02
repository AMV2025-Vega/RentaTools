#!/bin/sh
# Arranque: migra la BD, publica estáticos y lanza Gunicorn (nunca runserver en contenedores).
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --access-logfile - \
    --error-logfile -

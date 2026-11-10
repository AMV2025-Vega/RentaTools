# Monolito Django servido por Gunicorn sobre Alpine (imagen pequeña, usuario sin privilegios).
FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN addgroup -S app && adduser -S app -G app
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
# Normaliza finales de línea (Windows/CRLF) para que el script corra en Alpine.
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh \
    && mkdir -p /app/staticfiles && chown -R app:app /app

USER app
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]

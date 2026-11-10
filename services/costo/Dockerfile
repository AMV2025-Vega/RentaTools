# Microservicio Flask de costos, Gunicorn sobre Alpine.
FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN addgroup -S app && adduser -S app -G app
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
USER app
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "wsgi:app"]

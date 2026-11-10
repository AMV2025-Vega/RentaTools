"""Aplicación Celery: broker Redis para procesos de fondo (notificaciones, reportes)."""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("rentatools")
app.config_from_object("django.conf:settings", namespace="CELERY")
# Registra las tareas definidas en apps/reservas/infrastructure/tareas.py
app.autodiscover_tasks(["apps.reservas.infrastructure"], related_name="tareas")

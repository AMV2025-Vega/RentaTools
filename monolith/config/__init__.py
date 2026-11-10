# Garantiza que la app Celery se cargue al iniciar Django (para @shared_task).
from config.celery import app as celery_app

__all__ = ("celery_app",)

"""Implementaciones Django de los puertos transversales."""
from typing import Callable, ContextManager

from django.db import transaction
from django.utils import timezone

from apps.compartido.puertos import TransactionManager


class DjangoTransactionManager(TransactionManager):
    """Transacciones atómicas y callbacks post-commit con el ORM de Django."""

    def atomic(self) -> ContextManager:
        return transaction.atomic()

    def on_commit(self, callback: Callable[[], None]) -> None:
        transaction.on_commit(callback)


def hoy_local():
    """Reloj inyectable: fecha actual en la zona horaria del proyecto."""
    return timezone.localdate()

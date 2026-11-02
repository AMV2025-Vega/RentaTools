from django.db import DatabaseError, transaction
from django.test import TestCase

from apps.auditoria.models import RegistroAuditoria


class AuditoriaInmutableTests(TestCase):
    def setUp(self):
        self.reg = RegistroAuditoria.objects.create(accion="X", entidad="y", resultado="EXITO")

    def test_no_se_puede_actualizar(self):
        with self.assertRaises(DatabaseError), transaction.atomic():
            RegistroAuditoria.objects.filter(pk=self.reg.pk).update(accion="HACK")

    def test_no_se_puede_borrar(self):
        with self.assertRaises(DatabaseError), transaction.atomic():
            self.reg.delete()

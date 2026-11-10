from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    Usuario de la plataforma. Un mismo usuario puede publicar herramientas
    (propietario) y alquilar las de otros (cliente): por eso no hay campo `rol`.
    Se define desde el inicio porque cambiar AUTH_USER_MODEL después es muy costoso.
    """

    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True)

    REQUIRED_FIELDS = ["email"]

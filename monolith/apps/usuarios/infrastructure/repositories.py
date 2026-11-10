from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.compartido.excepciones import ReglaNegocioViolada
from apps.usuarios.application.ports import UsuarioRepository
from apps.usuarios.domain.entities import UsuarioDTO
from apps.usuarios.models import Usuario


class DjangoUsuarioRepository(UsuarioRepository):
    def existe_username(self, username: str) -> bool:
        return Usuario.objects.filter(username__iexact=username).exists()

    def existe_email(self, email: str) -> bool:
        return Usuario.objects.filter(email__iexact=email).exists()

    def crear(self, username: str, email: str, password: str, telefono: str) -> UsuarioDTO:
        try:
            # Las políticas de contraseña viven en settings (AUTH_PASSWORD_VALIDATORS).
            validate_password(password)
        except ValidationError as exc:
            raise ReglaNegocioViolada(" ".join(exc.messages), "password_debil") from exc
        u = Usuario.objects.create_user(username=username, email=email, password=password, telefono=telefono)
        return UsuarioDTO(id=u.id, username=u.username, email=u.email, telefono=u.telefono)

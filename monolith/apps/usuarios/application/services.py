from apps.compartido.excepciones import Conflicto, ReglaNegocioViolada
from apps.compartido.puertos import AuditLogger, EventoAuditoria
from apps.usuarios.application.ports import UsuarioRepository
from apps.usuarios.domain.entities import UsuarioDTO


class RegistroUsuarioService:
    """Caso de uso: registrar un usuario nuevo (SRP: solo orquesta el registro)."""

    def __init__(self, repo: UsuarioRepository, auditor: AuditLogger):
        self._repo = repo
        self._auditor = auditor

    def registrar(self, username: str, email: str, password: str, telefono: str = "") -> UsuarioDTO:
        username, email = username.strip(), email.strip().lower()
        if not username or not email:
            raise ReglaNegocioViolada("Usuario y correo son obligatorios.", "datos_incompletos")
        if self._repo.existe_username(username):
            raise Conflicto("El nombre de usuario ya está en uso.", "username_duplicado")
        if self._repo.existe_email(email):
            raise Conflicto("El correo ya está registrado.", "email_duplicado")

        usuario = self._repo.crear(username, email, password, telefono)
        self._auditor.registrar(
            EventoAuditoria(
                accion="USUARIO_REGISTRADO",
                entidad="usuario",
                entidad_id=str(usuario.id),
                resultado="EXITO",
                actor_id=usuario.id,
            )
        )
        return usuario

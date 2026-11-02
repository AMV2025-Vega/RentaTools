from abc import ABC, abstractmethod

from apps.usuarios.domain.entities import UsuarioDTO


class UsuarioRepository(ABC):
    @abstractmethod
    def existe_username(self, username: str) -> bool: ...

    @abstractmethod
    def existe_email(self, email: str) -> bool: ...

    @abstractmethod
    def crear(self, username: str, email: str, password: str, telefono: str) -> UsuarioDTO: ...

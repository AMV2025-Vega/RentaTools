from dataclasses import dataclass


@dataclass(frozen=True)
class UsuarioDTO:
    id: int
    username: str
    email: str
    telefono: str

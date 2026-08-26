from abc import ABC, abstractmethod


class NotificadorInterface(ABC):
    """
    Interfaz abstracta para los canales de notificación.
    """
    @abstractmethod
    def enviar_confirmacion(self, destinatario: str, mensaje: str) -> bool:
        pass


class EmailNotificador(NotificadorInterface):
    """
    Implementación concreta para notificaciones vía Email.
    """
    def enviar_confirmacion(self, destinatario: str, mensaje: str) -> bool:
        # Simulación de envío de correo empresarial
        print(f"[EMAIL ENVIADO a {destinatario}]: {mensaje}")
        return True


class SMSNotificador(NotificadorInterface):
    """
    Implementación concreta para notificaciones vía SMS.
    """
    def enviar_confirmacion(self, destinatario: str, mensaje: str) -> bool:
        # Simulación de envío de SMS
        print(f"[SMS ENVIADO a {destinatario}]: {mensaje}")
        return True


class NotificadorFactory:
    """
    Patrón Factory para instanciar la estrategia de notificación requerida.
    """
    @staticmethod
    def get_notificador(tipo: str = "EMAIL") -> NotificadorInterface:
        tipo_clean = tipo.upper()
        if tipo_clean == "EMAIL":
            return EmailNotificador()
        elif tipo_clean == "SMS":
            return SMSNotificador()
        else:
            raise ValueError(f"Tipo de notificación '{tipo}' no soportado.")
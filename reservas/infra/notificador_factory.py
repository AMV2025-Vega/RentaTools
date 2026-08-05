import os

class NotificadorFactory:
    @staticmethod
    def crear():
        if (os.getenv("ENV_TYPE") == "REAL"):
            return NotificadorSendGrid()
        return NotificadorConsola()

class NotificadorSendGrid:
    def enviar_confirmacion(self, reserva):
        # integración real con SendGrid
        pass

class NotificadorConsola:
    def enviar_confirmacion(self, reserva):
        print(f"[MOCK] Confirmación enviada para reserva {reserva.id}")
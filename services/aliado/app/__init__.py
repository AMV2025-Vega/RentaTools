"""
Servicio ALIADO simulado: "AseguraTools" (cotizador de seguros de alquiler).

Representa al servicio de OTRO equipo: RentaTools lo consume por HTTP a través de un
Adapter y no conoce nada de su implementación interna, solo el contrato (docs/contrato-aliado.md).
"""
import hmac
import os

from flask import Flask, jsonify, request

from app.routes import seguros_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["API_KEY"] = os.environ.get("ALIADO_API_KEY", "")
    app.register_blueprint(seguros_bp)

    @app.before_request
    def exigir_api_key():
        """Si hay clave configurada, toda ruta (menos /health) debe presentarla en X-API-Key."""
        clave = app.config["API_KEY"]
        if not clave or request.path == "/health":
            return None
        recibida = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(recibida.encode(), clave.encode()):
            return jsonify({"error": "no_autorizado", "message": "API key inválida o ausente."}), 401
        return None

    @app.get("/health")
    def health():
        return jsonify({"estado": "ok", "servicio": "aliado-seguros"})

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "solicitud_invalida", "message": getattr(e, "description", str(e))}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "no_encontrado", "message": "Recurso no encontrado."}), 404

    @app.errorhandler(405)
    def not_allowed(e):
        return jsonify({"error": "metodo_no_permitido", "message": "Método no permitido."}), 405

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "error_interno", "message": "Error interno del servidor."}), 500

    return app

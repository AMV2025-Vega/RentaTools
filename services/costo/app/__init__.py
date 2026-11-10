"""Microservicio de cálculo de costo de reservas (extraído del monolito: patrón Strangler)."""
from flask import Flask, jsonify

from app.routes import costo_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(costo_bp)

    @app.get("/health")
    def health():
        return jsonify({"estado": "ok", "servicio": "costo"})

    # Errores siempre en JSON, con la misma forma que el monolito espera: {"error", "message"}.
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

from flask import Flask, jsonify


def create_app():
    app = Flask(__name__)

    from app.routes import costo_bp

    app.register_blueprint(costo_bp)

    @app.errorhandler(400)
    def bad_request_handler(e):
        message = getattr(e, "description", "Solicitud inválida.")
        return (
            jsonify({"status": "error", "code": 400, "message": message}),
            400,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        return (
            jsonify(
                {
                    "status": "error",
                    "code": 500,
                    "message": "Ocurrió un error inesperado al procesar el cálculo.",
                }
            ),
            500,
        )

    return app
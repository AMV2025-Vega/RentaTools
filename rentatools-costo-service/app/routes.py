from app.services import CalculoError, calcular_costo_reserva
from flask import Blueprint, abort, jsonify, request

costo_bp = Blueprint("costo", __name__)


@costo_bp.route("/api/v2/reservas/costo/", methods=["POST"])
def calcular_costo():
    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="Se requiere un cuerpo JSON en la petición.")

    try:
        resultado = calcular_costo_reserva(data)
        return jsonify(resultado), 200
    except CalculoError as e:
        abort(400, description=str(e))
    except Exception as e:
        # Los errores no controlados son interceptados por el errorhandler 500 de Flask
        raise e
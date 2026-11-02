from flask import Blueprint, abort, jsonify, request

from app.services import CalculoError, calcular_costo_reserva

costo_bp = Blueprint("costo", __name__)


@costo_bp.route("/api/v2/reservas/costo/", methods=["POST"])
def calcular_costo():
    """Capa HTTP: solo parsea la petición y delega en el servicio."""
    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="Se requiere un cuerpo JSON en la petición.")
    try:
        return jsonify(calcular_costo_reserva(data)), 200
    except CalculoError as e:
        abort(400, description=str(e))

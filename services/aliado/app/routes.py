from flask import Blueprint, abort, jsonify, request

from app.services import CotizacionError, cotizar_seguro

seguros_bp = Blueprint("seguros", __name__)


@seguros_bp.route("/api/v1/seguros/cotizar", methods=["POST"])
def cotizar():
    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="Se requiere un cuerpo JSON.")
    try:
        return jsonify(cotizar_seguro(data)), 200
    except CotizacionError as e:
        abort(400, description=str(e))

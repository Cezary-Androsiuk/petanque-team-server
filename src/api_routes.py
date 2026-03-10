from flask import Blueprint, request, jsonify
from src.api.methods import handle_authenication_request, handle_add_data_request
from time import sleep

from src.utils.Log import I, W, E, D, R

api_bp = Blueprint('api', __name__, url_prefix="/api")

@api_bp.route('/', methods=['POST', 'GET'])
def handle_request():
    I(request)
    I(request.headers)
    I(request.data)
    I(request.remote_addr)
    I(request.environ)

    sleep(0.5) # speed is not required - brute froce protection and login delay

    user_agent = request.headers.get('User-Agent') == 'PetanqueTeam/1.0'
    content_type = request.headers.get('Content-Type') == 'application/json'
    if not user_agent or not content_type:
        W("Unauthorized client")
        return jsonify(
            {
                "status": "error", 
                "message": "Unauthorized client"
            }), 403

    # parse JSON data
    json_data = None
    try:
        json_data = request.get_json()
    except Exception as e:
        W(f"Invalid JSON, details: ", str(e))
        return jsonify({
            "status": "error",
            "message": "Invalid JSON",
            "details": str(e)
        }), 400
    
    if json_data is None:
        W("Invalid JSON")
        return jsonify({
            "status": "error",
            "message": "Invalid JSON"
        }), 400
    

    action = json_data['action']
    if action == 'auth':
        return handle_authenication_request(json_data, request)
    elif action == 'add_data':
        return handle_add_data_request(json_data, request);

    W("Invalid action")
    return jsonify({
        "status": "error",
        "message": "Invalid action"
    }), 422
    
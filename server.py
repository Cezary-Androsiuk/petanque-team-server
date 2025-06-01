from flask import Flask, request, jsonify, Response, render_template
from methods import handle_authenication_request, handle_add_data_request
from constants import DEBUG
import re

from Log import I, W, E, D, R

app = Flask(__name__)

@app.route('/api', methods=['POST', 'GET'])
def handle_request():
    I(request)
    I(request.headers)
    I(request.data)
    I(request.remote_addr)
    I(request.environ)

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
    

@app.route('/')
def home():
    html_content = """
        <html>
            <body>
                <h1>Hello, World!</h1>
            </body>
        </html>
    """
    return Response(html_content, mimetype='text/html')

@app.route('/template')
def template():
    return render_template('index.html', name='World')

if __name__ == '__main__':
    # HTTP
    app.run(host='0.0.0.0', port=5000, debug=DEBUG)
    
    # HTTPS - dummy
    # openssl req -x500 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
    # context = ('cert.pem', 'key.pem')
    # app.run(host='0.0.0.0', port=5000, ssl_context=context)

# python -m venv env
# env\Scripts\activate
# pip install -r requirements.txt
# python server.py

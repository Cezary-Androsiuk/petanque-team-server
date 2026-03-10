from flask import Flask
import os

from src.api_routes import api_bp
from src.webpage_routes import webpage_bp

from src.utils.constants import DEBUG

app = Flask(__name__)


app.register_blueprint(api_bp)

app.register_blueprint(webpage_bp)

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

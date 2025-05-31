from flask import Flask, request, jsonify, Response, render_template

app = Flask(__name__)

@app.route('/api', methods=['POST', 'GET'])
def handle_request():
    print("Request:", request)
    print("Headers:", request.headers)
    print("Data:", request.data)

    data = None
    try:
        data = request.get_json()
    except Exception as e:
        print("exception: ",e)
    
    if data is None:
        return "No data received", 400
    
    print("Received request")

    response_data = {
        "status": "success",
        "received_data": "" if data is None else data,
        "message": "Server works!"
    }

    return jsonify(response_data), 200

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
    app.run(host='0.0.0.0', port=5000)
    
    # HTTPS - dummy
    # openssl req -x500 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
    # context = ('cert.pem', 'key.pem')
    # app.run(host='0.0.0.0', port=5000, ssl_context=context)

# python -m venv env
# env\Scripts\activate
# pip install -r requirements.txt
# python server.py

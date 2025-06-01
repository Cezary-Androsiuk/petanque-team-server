from flask import Request, jsonify, render_template
import json
from constants import DEBUG

from Log import I, W, E, D, R

example_credentials = {
    'login': 'example login',
    'password_hash': 'ee7ed3c8af7ac48bd459b901a1f8fd3e8f4d1701f6a6cd588ca70849a4619d2b3c79ab60c4ee0538141d48fc4f3934e6e30668c994b2aeba352c7259831d5a50' # 'example password'
}

def authenticate_credentials(login: str, password_hash: str):
    if DEBUG:
        correct_login = login == example_credentials['login']
        correct_password = password_hash == example_credentials['password_hash']
        return correct_login and correct_password
    


def handle_authenication_request(json_data, request : Request = None):
    login, password_hash = json_data['login'], json_data['password_hash']
    if login is None or password_hash is None:
        W("Invalid JSON - missing credentials")
        return jsonify({
            "status": "error",
            "message": "Invalid JSON",
            "details": "missing credentials"
        }), 400
    
    authenticated = authenticate_credentials(login, password_hash)
    status = "success" if authenticated else "failed"
    I('Credentials authentication: %d', status)

    response_data = {
        "status": status
        # session key that can be used as a seed for data encryption or something
    }
    I('response: %s', response_data)
    return jsonify(response_data), 200

def save_new_data(json_data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False,  separators=(",", ":"))
        # json.dump(json_data, f, ensure_ascii=False, indent=4)

def handle_add_data_request(json_data, request : Request = None):
    login, password_hash = json_data['login'], json_data['password_hash']
    if login is None or password_hash is None:
        W("Invalid JSON - missing credentials")
        return jsonify({
            "status": "error",
            "message": "Invalid JSON",
            "details": "missing credentials"
        }), 400
    
    authenticated = authenticate_credentials(login, password_hash)
    status = "success" if authenticated else "failed"
    I('Credentials authentication: %d', status)

    if authenticated:
        new_data = json_data['data']
        if new_data is None:
            W("Invalid JSON - missing data")
            return jsonify({
                "status": "error",
                "message": "Invalid JSON",
                "details": "missing data"
            }), 400
        
        save_new_data(new_data)
        
    response_data = {
        "status": status
    }
    I('response: %s', response_data)
    return jsonify(response_data), 200
        


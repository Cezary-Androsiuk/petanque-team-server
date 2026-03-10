from flask import Blueprint, current_app, render_template, send_from_directory
import os

webpage_bp = Blueprint('webpage', __name__, url_prefix="/")

# @webpage_bp.route('/icons/PetanqueTeam.ico')
# def favicon():
#     return send_from_directory(os.path.join(current_app.root_path, 'static'),
#                                'favicon.ico', mimetype='image/vnd.microsoft.icon')

@webpage_bp.route('/')
def home():
    return render_template('home.html')

@webpage_bp.route('/matches')
def matches():
    example_matches = [
        { "match_title": "match 1", "highlighted": True},
        { "match_title": "match 2", "highlighted": False},
        { "match_title": "match 3", "highlighted": True},
        { "match_title": "match 4", "highlighted": False},
    ]

    return render_template('matches.html', matches=example_matches)

@webpage_bp.route('/info')
def info():
    return render_template('info.html')

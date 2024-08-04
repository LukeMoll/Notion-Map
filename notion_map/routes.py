"""
    Flask route definitions.

    Exports 'app' (WSGI-compatible Flask application)
"""

__all__ = ['app']

from flask import Flask, request, send_file
from .notion import get_geojson

app = Flask(__name__)


import os
HTML_DIR = os.path.join(os.path.dirname(__file__), "html")

@app.route("/")
def index():
    return send_file(os.path.join(HTML_DIR, "index.html"))

@app.route("/api/geojson")
def geojson():
    if 'database_id' not in request.args:
        return "Missing parameter 'database_id'", 422

    if 'coord_col' not in request.args:
        return "Missing parameter 'coord_col'", 422

    database_id = request.args.get('database_id')
    coord_col = request.args.get('coord_col')
    name_col = request.args.get('name_col')
    url_col = request.args.get('url_col')

    try:
        result = get_geojson(database_id, coord_col, name_column_name=name_col, url_column_name=url_col)

        return result

    except RuntimeError as e:
        print(e)
        return str(e), 500

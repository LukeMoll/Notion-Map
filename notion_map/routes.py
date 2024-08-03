from flask import Flask, request

app = Flask(__name__)

from .notion import get_geojson


# TODO: replace with serve_static
import os
this_dir = os.path.dirname(__file__)

@app.route("/")
def index():
    with open(os.path.join(this_dir, "html", "index.html")) as fd:
        return fd.read()

@app.route("/api/geojson")
def geojson():
    if 'database_id' not in request.args:
        return {
            "error": "Missing parameter 'database_id'",
            "code": 422
        }, 422

    if 'coord_col' not in request.args:
        return {
            "error": "Missing parameter 'coord_col'",
            "code": 422
        }, 422

    database_id = request.args.get('database_id')
    coord_col = request.args.get('coord_col')
    name_col = request.args.get('name_col')
    url_col = request.args.get('url_col')

    try:
        result = get_geojson(database_id, coord_col, name_column_name=name_col, url_column_name=url_col)

        return result

    except RuntimeError as e:
        print(e)
        return {
            "error": str(e),
            "code": 500
        }, 500

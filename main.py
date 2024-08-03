# Make sure NOTION_KEY is set before starting the app.
import os

try:
    # dotenv doesn't build on my machine, but we've only got the one variable anyway.

    # secrets.py alongside main.py
    # mainly for development
    import secrets

    os.environ['NOTION_KEY'] = secrets.NOTION_KEY
except ImportError: pass
except AttributeError: pass

if 'NOTION_KEY' not in os.environ:
    print("Environment variable $NOTION_KEY not set.")
    exit(1)


# https://www.devdungeon.com/content/run-python-wsgi-web-app-waitress
from waitress import serve

# import notion-map app
from notion_map import app

# TODO: allow environment variable to override.
serve(app, host='0.0.0.0', port=8000)
"""
    Entry point for Nixpacks - not required if you're using a different WSGI server.
"""

# Make sure NOTION_KEY is set before starting the app.
import os

try:
    # dotenv doesn't build on my machine, but we've only got the one variable anyway.

    # secrets.py alongside main.py - mainly convenient for development.
    import secrets

    os.environ['NOTION_KEY'] = secrets.NOTION_KEY
except ImportError: pass
except AttributeError: pass

if 'NOTION_KEY' not in os.environ:
    print("Environment variable $NOTION_KEY not set.")
    exit(1)


# Run a production-ready server (Waitress)
# https://www.devdungeon.com/content/run-python-wsgi-web-app-waitress
from waitress import serve

# import WSGI app
from notion_map import app

port = os.environ.get('PORT', 8000)
print(f"Serving on {port}...")
serve(app, host='0.0.0.0', port=port)
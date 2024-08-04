"""
    Methods to interact with the Notion API.
"""

__all__ = ['get_geojson']

from notion_client import Client
from notion_client.errors import APIResponseError

import os
NOTION_KEY = os.environ['NOTION_KEY']
notionClient = Client(auth=NOTION_KEY)
def test_auth():
    """
        Function to keep these variables out of global scope.
    """
    try:
        result = notionClient.users.me()
        print(f"Authenticated to Notion as '{result['name']}'")
    except APIResponseError as e:
        print("Tried to test Notion API key, got API error:")
        print(f"{e.status} {e.code}: '{str(e)}'")
        exit(1)

test_auth()

def get_geojson(notion_database_id : str, coordinate_column_name:str, name_column_name=None, url_column_name=None) -> dict:
    """
        Fetch a Notion database and construct a GeoJSON FeatureCollection from the rows within. This is the main processing on the Python side.

        The database must exist AND the Integration must have access to it. In Notion, this is done with the 'Connect To' option on a Page.
        The coordinates must be given in decimal degrees of Latitude followed by Longitude. Minor errors that only affect single rows will
        generate a Warning in the output object. Major errors that prevent a valid result being produced will raise a RuntimeError.

        Args:
            notion_database_id (str): ID of the Notion Database. This can be found in the URL.
            coordinate_column_name (str): Name of the database column (Text type) that holds coordinates.
            name_column_name (str): Name of the database column (Text or Title type) to be used to name each Feature. 
                                    If None, then the Title column will be used.
            url_column_name (str): Name of the database column (URL type) to provide a clickable link on each Feature.

        Returns:
            GeoJSON FeatureCollection, as a dict. Each Feature also contains 'name' and 'url' properties.
            The top-level object contains 'database_name' and 'database_url' properties.
            Additionally, the top-level object may contain a list of 'warnings' strings that were raised
            during generation.
    """

    try:
        # Running this may raise a few errors; we're mainly interested in provoking a 403 or 404 response.
        result = notionClient.databases.retrieve(database_id=notion_database_id)

        # Check that the coordinate column exists and is a suitable type
        if coordinate_column_name not in result["properties"]:
            raise RuntimeError(f"Coordinate column '{coordinate_column_name}' not found!")
        
        if result["properties"][coordinate_column_name]["type"] != "rich_text":
            t = result["properties"][coordinate_column_name]["type"]
            raise RuntimeError(f"Invalid type '{t}' for coordinate column '{coordinate_column_name}'; expected 'rich_text'.")

        # Find a name column:
        if name_column_name != None:
            # Either the one specified
            # Check it exists
            if name_column_name not in result["properties"]:
                raise RuntimeError(f"Name column '{name_column_name}' not found!")

            # and has a suitable type
            name_column_type = result["properties"][name_column_name]["type"]
            if name_column_type != "rich_text" and name_column_type != "title":
                raise RuntimeError(f"Invalid type '{t}' for name column '{name_column_name}'")
        else:
            # Or try to find the Title property (which there should be exactly one of)
            for prop in result["properties"].values():
                if prop["type"] == "title":
                    name_column_name = prop["name"]
            if name_column_name == None:
                raise RuntimeError("Could not find a Title column and no Name column specified!")

        # Check the URL column exists and is a suitable type, if specified
        if url_column_name is not None:
            if url_column_name not in result["properties"]:
                raise RuntimeError(f"Specified URL column '{url_column_name}' not found!")
            
            if (t := result["properties"][url_column_name]["type"]) != "url":
                raise RuntimeError(f"Invalid type '{t}' for URL column '{url_column_name}'")

    except APIResponseError as e:
        if e.status == 403:
            raise RuntimeError(f"Notion API error {e.status} {e.code} '{str(e)}' Does the integration have access to the database specified?")
        elif e.status == 404:
            raise RuntimeError(f"Notion API error {e.status} {e.code} '{str(e)}'")
        else:
            print(f"Notion API error {e.status} {e.code}\n'{str(e)}'")
            print(f"{notion_database_id=}")
            raise RuntimeError(f"Notion API error {e.status} {e.code} '{str(e)}'")

    geojson = {
        "type": "FeatureCollection",
        "features": [],
        "warnings": [],
        "database_name": to_plain_text(result["title"]),
        "database_url": result["url"]
    }

    try:
        # Is it possible to restrict returned columns to only the ones we want?
        query_res = notionClient.databases.query(notion_database_id)

        for row in query_res['results']:
            p_name = row['properties'][name_column_name]
            p_coords = row['properties'][coordinate_column_name]
            p_url = row['properties'][url_column_name] if url_column_name is not None else None
            
            if "rich_text" in p_name:
                name = to_plain_text(p_name["rich_text"])
            elif "title" in p_name:
                name = to_plain_text(p_name["title"])

            # Decode coordinates into lattitude and longitude
            try:
                s_coords = to_plain_text(p_coords['rich_text'])
                parts = s_coords.split(",")
                if len(parts) != 2:
                    geojson['warnings'].append(f"Invalid coordinates for '{name}': '{s_coords}'. Ommitting row.")
                    continue

                lattitude = float(parts[0])
                longitude = float(parts[1])

                if (not (-90.0 <= lattitude <= +90.0)) or (not (-180.0 <= longitude <= +180.0)):
                    geojson['warnings'].append(f"Coordinates out-of-range for '{name}': {lattitude},{longitude}. Ommitting row.")
                    continue

            except IndexError:
                geojson['warnings'].append(f"Could not get coordinates for '{name}'. Ommitting row.")
                continue

            except ValueError:
                geojson['warnings'].append(f"Could not parse coordinates for '{name}': '{s_coords}'. Ommitting row.")
                continue

            geojson["features"].append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [longitude, lattitude]
                    # https://datatracker.ietf.org/doc/html/rfc7946#section-3.1.1
                    # Note! Not the "traditional" latt,long order, for reasons explained here:
                    # https://macwright.com/2015/03/23/geojson-second-bite#position
                },
                "properties": {
                    "name": name
                }
            })

            if p_url is not None and p_url['url'] != None and len(p_url['url']) > 0:
                # Blank fields can be None instead of empty.
                geojson['features'][-1]['properties']['url'] = p_url['url']

    except APIResponseError as e:
        raise e

    if len(geojson['warnings']) == 0:
        del geojson['warnings']

    return geojson

def to_plain_text(rich_text_block : list[dict]) -> str:
    """
        Takes an array of 0 or more Rich Text objects and concatenates their plain_text properties.
    """

    if type(rich_text_block) != list:
        raise TypeError(f"Invalid type {type(rich_text_block)}, expecting list.")

    buf = ""

    for d in rich_text_block:
        if type(d) != dict:
            raise TypeError(f"Invalid element type {type(d)} in list, expecting dict.")

        buf += d['plain_text']

    return buf        


# Server-less test mode
if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        db_id = sys.argv[1]
        coord_col = sys.argv[2]
        if len(sys.argv) >= 4:
            url_col = sys.argv[3]
        else:
            url_col = None
        print(f"Looking up Database ID {db_id} using coordinates from column '{coord_col}', URLs from column '{url_col}'")
    else:
        print("USAGE: <Database ID> <Coordinates column name> [URL column name]")
        exit(1)

    from pprint import pp

    pp(get_geojson(db_id, coord_col, url_column_name=url_col))
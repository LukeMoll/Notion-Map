from notion_client import Client
from notion_client.errors import APIResponseError

import os
NOTION_KEY = os.environ['NOTION_KEY']
notionClient = Client(auth=NOTION_KEY)
def test_auth():
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
        TODO:
    """

    try:
        # Check this doesn't return 401 or 404
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
        # TODO: differentiate between forbidden and not found
        raise e

    geojson = {
        "type": "FeatureCollection",
        "features": [],
        "warnings": [],
        "database_name": result["title"][0]["plain_text"],
        "database_url": result["url"]
    }

    try:
        # TODO: restrict columns
        query_res = notionClient.databases.query(notion_database_id)

        for row in query_res['results']:
            p_name = row['properties'][name_column_name]
            p_coords = row['properties'][coordinate_column_name]
            p_url = row['properties'][url_column_name] if url_column_name is not None else None
            
            # TODO: better.
            if "rich_text" in p_name:
                name = p_name["rich_text"][0]["plain_text"]
            elif "title" in p_name:
                name = p_name["title"][0]["plain_text"]

            # Decode coordinates into lattitude and longitude
            # TODO: replace with method to get 0+ rich_text parts and stich together the plain_text parts.
            try:
                s_coords = p_coords['rich_text'][0]['plain_text']
                parts = s_coords.split(",")
                if len(parts) != 2:
                    warnings.append(f"Invalid coordinates for '{name}': '{s_coords}'. Ommitting row.")
                    continue

                lattitude = float(parts[0])
                longitude = float(parts[1])

                if (not (-90.0 <= lattitude <= +90.0)) or (not (-180.0 <= longitude <= +180.0)):
                    warnings.append(f"Coordinates out-of-range for '{name}': {lattitude},{longitude}. Ommitting row.")
                    continue

            except IndexError:
                warnings.append(f"Could not get coordinates for '{name}'. Ommitting row.")
                continue

            except ValueError:
                warnings.append(f"Could not parse coordinates for '{name}': '{s_coords}'. Ommitting row.")
                continue

            # TODO: get URL too.

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

    except APIResponseError as e:
        raise e

    if len(geojson['warnings']) == 0:
        del geojson['warnings']

    return geojson


# Server-less test mode
if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3:
        db_id = sys.argv[1]
        coord_col = sys.argv[2]
        print(f"Looking up Database ID {db_id} using coordinates from column '{coord_col}'")
    else:
        print("USAGE: <Database ID> <Coordinates column name>")
        exit(1)

    from pprint import pp

    pp(get_geojson(db_id, coord_col))
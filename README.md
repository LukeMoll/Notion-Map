Notion Map
===
Displays points on a map, sourcing from a Notion Database.

## Installation
Get a Notion API key. Set environment variable NOTION_KEY to the key (or edit `secrets.example.py` and rename to `secrets.py`). Run `main.py`. Server will listen on HTTP 8000 by default (overridable with the PORT environment variable).

## Usage
```
http://<your-server>:8000/?database_id=...&coord_col=...&name_col=...&url_col=...
```
* Database ID: see [Retrieve a database](https://developers.notion.com/reference/retrieve-a-database)
* Coordinate column: Name of the column (Rich Text type) with decimal degrees Latitude, Longitude.
* Name column (optional): Name of the column (Rich Text or Title type) with names that will be displayed next to the points. By default, uses the Title column.
* URL column (optional): Name of the column (URL type) that will add hyperlinks to the points.

---
Distributed under BSD 3-Clause.

logo.png includes elements from [Hendrik Hermawan](https://thenounproject.com/icon/map-7080160/) (CC-BY 3.0)
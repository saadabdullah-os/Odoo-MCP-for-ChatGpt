import json
from main import app

def export_schema():
    openapi_schema = app.openapi()
    with open("openapi.json", "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    print("Successfully exported openapi.json for ChatGPT Custom Actions!")

if __name__ == "__main__":
    export_schema()

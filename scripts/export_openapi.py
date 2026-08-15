
import json
import os
from src.api.main import app

def export_openapi():
    os.makedirs('docs', exist_ok=True)
    schema = app.openapi()
    with open('docs/openapi.json', 'w') as f:
        json.dump(schema, f, indent=2)
    print("Exported openapi.json")

if __name__ == "__main__":
    export_openapi()

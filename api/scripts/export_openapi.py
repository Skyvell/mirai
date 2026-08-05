"""Print the FastAPI OpenAPI schema as JSON.

The frontend generates its API client from this output (pnpm generate:api).
Importing the app has no side effects: settings default, engine and agent are lazy.
"""

import json

from mirai_api.main import app

print(json.dumps(app.openapi()))

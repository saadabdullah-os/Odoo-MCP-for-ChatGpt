"""
Entry point for local development and OpenAPI export.
Imports the FastAPI application from api.index.
"""
from api.index import app, odoo, GPT_SECRET_TOKEN

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

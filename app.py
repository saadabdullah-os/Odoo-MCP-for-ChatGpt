import gradio as gr
from main import app as fastapi_app

# Interactive dashboard for Hugging Face Space visitors
with gr.Blocks(title="Flow ERP - Odoo Middleware") as demo:
    gr.Markdown("# 🚀 Flow ERP — Odoo Supply Chain Read-Only API")
    gr.Markdown("### Secure bridge connecting ChatGPT to OneScreen's Colombia Odoo ERP")
    gr.Markdown(
        """
        - **Status:** Online & Ready
        - **Authentication:** Bearer token required on all data endpoints
        - **Endpoints:**
          - `GET /activities/overdue`
          - `GET /pos/open`
          - `GET /pos/{po_name}`
          - `GET /rmas/open`
          - `GET /rmas/{rma_name}`
          - `GET /openapi.json`
        """
    )

# Mount Gradio dashboard at /ui while keeping root API routes clean
app = gr.mount_gradio_app(fastapi_app, demo, path="/ui")

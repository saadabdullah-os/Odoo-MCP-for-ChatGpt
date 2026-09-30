import os
import sys
import logging

try:
    import xmlrpc.client
    from datetime import datetime
    from typing import Optional, List, Dict, Any
    from fastapi import FastAPI, Depends, HTTPException, Security, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from dotenv import load_dotenv

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger("flow_odoo_middleware")

    load_dotenv()

    # Server-Side Secrets
    ODOO_URL = os.environ.get("ODOO_URL", "https://erp.onescreenlatam.com")
    ODOO_DB = os.environ.get("ODOO_DB", "claryicon-master-7426961")
    ODOO_USERNAME = os.environ.get("ODOO_USERNAME")
    ODOO_API_KEY = os.environ.get("ODOO_API_KEY", "9f2da2949576a5cdf548303c43aa7a85884c8c95")
    GPT_SECRET_TOKEN = os.environ.get("GPT_SECRET_TOKEN", "Colombia_Flow_2026")
    DEFAULT_RMA_MODEL = os.environ.get("ODOO_RMA_MODEL", "rma.ticket")


    class OdooConnection:
        def __init__(self):
            self.common = None
            self.models = None
            self.uid: Optional[int] = None
            self.rma_model: str = DEFAULT_RMA_MODEL
            self._connected = False

        def connect(self) -> int:
            username = os.environ.get("ODOO_USERNAME") or ODOO_USERNAME
            api_key = os.environ.get("ODOO_API_KEY") or ODOO_API_KEY
            odoo_url = os.environ.get("ODOO_URL") or ODOO_URL
            odoo_db = os.environ.get("ODOO_DB") or ODOO_DB

            if not username:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ODOO_USERNAME is not configured on the server. Please set it in Environment Variables."
                )
            try:
                self.common = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/common", allow_none=True)
                self.uid = self.common.authenticate(odoo_db, username, api_key, {})
                if not self.uid:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Odoo Authentication Failed. Please verify ODOO_USERNAME and ODOO_API_KEY."
                    )
                self.models = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/object", allow_none=True)
                self._connected = True
                logger.info("Successfully authenticated with Odoo (UID: %s)", self.uid)
                return self.uid
            except HTTPException:
                raise
            except Exception as e:
                logger.error("Failed to connect to Odoo: %s", e)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Could not reach Odoo server: {str(e)}"
                )

        def ensure_connected(self):
            if not self._connected or not self.uid:
                self.connect()

        def search_read(self, model: str, domain: list, fields: list, limit: int = 15) -> List[Dict[str, Any]]:
            self.ensure_connected()
            odoo_db = os.environ.get("ODOO_DB") or ODOO_DB
            api_key = os.environ.get("ODOO_API_KEY") or ODOO_API_KEY
            try:
                return self.models.execute_kw(
                    odoo_db, self.uid, api_key,
                    model, 'search_read', [domain],
                    {'fields': fields, 'limit': limit}
                )
            except Exception as e:
                logger.error("Odoo search_read error on model '%s': %s", model, e)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Odoo query error on model '{model}': {str(e)}"
                )


    odoo = OdooConnection()

    app = FastAPI(
        title="Flow ERP - Odoo Supply Chain Read-Only API",
        description="Secure, read-only bridge connecting ChatGPT to OneScreen's Colombia Odoo ERP.",
        version="1.0.0"
    )

    security = HTTPBearer(
        description="Bearer token authentication. Enter your GPT_SECRET_TOKEN."
    )


    def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
        secret = os.environ.get("GPT_SECRET_TOKEN") or GPT_SECRET_TOKEN
        if not credentials or credentials.credentials != secret:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing ChatGPT Bearer token."
            )
        return credentials.credentials


    @app.middleware("http")
    async def strip_vercel_prefix(request, call_next):
        """Normalizes path using Vercel's x-matched-path header or cleans rewrite prefixes."""
        matched_path = request.headers.get("x-matched-path")
        if matched_path:
            if "?" in matched_path:
                matched_path = matched_path.split("?")[0]
            request.scope["path"] = matched_path
        else:
            path = request.scope.get("path", "")
            if path.startswith("/api/index.py"):
                request.scope["path"] = path[len("/api/index.py"):] or "/"
            elif path.startswith("/api"):
                request.scope["path"] = path[len("/api"):] or "/"
        return await call_next(request)


    # ==========================================
    # HEALTH & INFO ENDPOINTS
    # ==========================================

    @app.get("/", tags=["System"], summary="Root", operation_id="root")
    def root():
        """Service status and readiness check."""
        return {
            "status": "online",
            "service": "Flow ERP - Odoo Supply Chain Read-Only API",
            "version": "1.0.0",
            "odoo_connected": odoo._connected,
            "rma_model": odoo.rma_model
        }


    @app.get("/health", tags=["System"], summary="Health Check", operation_id="health_check")
    def health_check():
        """Health check for external monitoring."""
        return {"status": "healthy"}


    # ==========================================
    # EXPOSED TOOLS & ENDPOINTS
    # ==========================================

    @app.get(
        "/activities/overdue",
        dependencies=[Depends(verify_token)],
        tags=["Supply Chain Activities"],
        summary="Get overdue activities",
        operation_id="get_overdue_activities"
    )
    def get_overdue_activities():
        """Fetches Supply Chain activities where the deadline is in the past."""
        today = datetime.today().strftime('%Y-%m-%d')
        domain = [['date_deadline', '<', today]]
        fields = ['res_name', 'res_model', 'summary', 'date_deadline', 'user_id', 'activity_type_id']
        return odoo.search_read('mail.activity', domain, fields, limit=25)


    @app.get(
        "/pos/open",
        dependencies=[Depends(verify_token)],
        tags=["Purchase Orders"],
        summary="Get open purchase orders",
        operation_id="get_open_purchase_orders"
    )
    def get_open_purchase_orders():
        """Fetches open Colombia Purchase Orders (draft, sent, purchase)."""
        domain = [['state', 'in', ['draft', 'sent', 'purchase']]]
        fields = ['name', 'partner_id', 'date_order', 'amount_total', 'state']
        return odoo.search_read('purchase.order', domain, fields, limit=25)


    @app.get(
        "/pos/{po_name}",
        dependencies=[Depends(verify_token)],
        tags=["Purchase Orders"],
        summary="Get purchase order details",
        operation_id="get_purchase_order_details"
    )
    def get_purchase_order_details(po_name: str):
        """Fetches exact details of a specific Purchase Order by name (e.g., P00012), including line items, quantities, and prices."""
        domain = [['name', '=', po_name]]
        fields = ['name', 'partner_id', 'date_planned', 'amount_total', 'state', 'order_line']
        result = odoo.search_read('purchase.order', domain, fields, limit=1)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Purchase Order '{po_name}' not found")
        
        po = result[0]
        
        # Expand order_line IDs into detailed line item records if available
        line_ids = po.get('order_line', [])
        if line_ids and isinstance(line_ids, list):
            try:
                line_fields = ['id', 'name', 'product_id', 'product_qty', 'price_unit', 'price_subtotal']
                lines = odoo.search_read('purchase.order.line', [['id', 'in', line_ids]], line_fields, limit=50)
                po['order_lines_detail'] = lines
            except Exception as e:
                logger.warning("Could not fetch purchase.order.line details for PO %s: %s", po_name, e)
                po['order_lines_detail'] = []

        return po


    @app.get(
        "/rmas/open",
        dependencies=[Depends(verify_token)],
        tags=["RMAs"],
        summary="Get open RMAs",
        operation_id="get_open_rmas"
    )
    def get_open_rmas():
        """Fetches open RMAs from the rma_from_forms module."""
        model = odoo.rma_model or DEFAULT_RMA_MODEL
        if model == 'rma.ticket':
            domain = [['stage_id.name', '!=', 'Solved']]
            fields = ['name', 'partner_id', 'customer_name', 'stage_id', 'device_model', 'create_date']
        else:
            domain = [['state', 'not in', ['done', 'cancel']]]
            fields = ['name', 'partner_id', 'create_date', 'state']
        return odoo.search_read(model, domain, fields, limit=25)


    @app.get(
        "/rmas/{rma_name}",
        dependencies=[Depends(verify_token)],
        tags=["RMAs"],
        summary="Get RMA details",
        operation_id="get_rma_details"
    )
    def get_rma_details(rma_name: str):
        """Fetches exact details of a specific RMA by name."""
        model = odoo.rma_model or DEFAULT_RMA_MODEL
        domain = [['name', '=', rma_name]]
        if model == 'rma.ticket':
            fields = [
                'name', 'partner_id', 'customer_name', 'stage_id',
                'device_model', 'device_serial', 'warranty_status',
                'failure_description', 'proposed_solution', 'repair_date_text',
                'drive_url', 'notes', 'create_date'
            ]
        else:
            fields = ['name', 'partner_id', 'state', 'description']
        result = odoo.search_read(model, domain, fields, limit=1)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"RMA '{rma_name}' not found")
        return result[0]

except Exception as _e:
    import traceback
    _err_msg = traceback.format_exc()
    logging.error("Fatal startup error in api/index.py:\n%s", _err_msg)

    async def app(scope, receive, send):
        """ASGI fallback handler that displays startup errors in browser/client."""
        if scope['type'] == 'http':
            await send({
                'type': 'http.response.start',
                'status': 500,
                'headers': [[b'content-type', b'text/plain; charset=utf-8']],
            })
            await send({
                'type': 'http.response.body',
                'body': f"FastAPI Serverless Startup Error:\n\n{_err_msg}".encode('utf-8'),
            })

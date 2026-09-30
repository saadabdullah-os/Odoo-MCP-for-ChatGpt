# Flow ERP — Odoo Supply Chain Read-Only Middleware

A secure, high-performance FastAPI middleware bridging **ChatGPT** (via Custom GPT Actions) and **OneScreen's Odoo ERP** (Colombia / LATAM instance).

---

## 🛡️ Security & Architecture Guarantees

1. **Strict Server-Side Credential Isolation:**
   - The Odoo API key, database name, and username are stored strictly in server-side environment variables (`.env`).
   - They are **never** exposed to the ChatGPT client, the OpenAPI schema, or web responses.
2. **Read-Only Guarantee:**
   - The integration exclusively invokes Odoo's XML-RPC `search_read` method.
   - No `create`, `write`, `unlink`, or modifying methods are present in the codebase.
3. **ChatGPT Bearer Authentication:**
   - Every data endpoint requires ChatGPT to provide a `Bearer` token (`GPT_SECRET_TOKEN`) in the `Authorization` header (`Authorization: Bearer <TOKEN>`).
   - Unauthorized requests return HTTP 403 Forbidden.
4. **Dynamic RMA Model Detection:**
   - The middleware inspects Odoo's `ir.model` registry upon startup to automatically identify the technical model for the `rma_from_forms` module (`rma.form`, `rma.request`, `x_rma`, etc.) with fallback to `rma.form` or explicit `.env` override.

---

## 🛠️ Exposed Tools & Data Dictionary

| Tool / Operation ID | HTTP Route | Input Parameters | Output / Response |
| :--- | :--- | :--- | :--- |
| `get_overdue_activities` | `GET /activities/overdue` | *None* | Array of overdue activities (`res_name`, `res_model`, `summary`, `date_deadline`, `user_id`, `activity_type_id`). |
| `get_open_purchase_orders` | `GET /pos/open` | *None* | Array of open POs (`name`, `partner_id`, `date_order`, `amount_total`, `state`). |
| `get_purchase_order_details` | `GET /pos/{po_name}` | `po_name` (String, e.g. `P00012`) | Detailed PO record with line items, quantities, and unit prices. |
| `get_open_rmas` | `GET /rmas/open` | *None* | Array of open RMAs (`name`, `partner_id`, `create_date`, `state`). |
| `get_rma_details` | `GET /rmas/{rma_name}` | `rma_name` (String) | Detailed RMA record including status, partner, and description. |
| `health_check` | `GET /health` | *None* | Health status check for host monitoring (`status: healthy`). |
| `root` | `GET /` | *None* | Service info, Odoo connection status, and active RMA model. |

---

## 📁 Repository Structure

```
ODOO/
├── .env                  # Server secrets (NEVER commit to git)
├── .env.example          # Environment variable template
├── .gitignore            # Git exclusion rules
├── requirements.txt      # Python dependencies
├── main.py               # Complete FastAPI middleware server
├── export_openapi.py     # Utility to export openapi.json for ChatGPT
├── openapi.json          # Pre-generated OpenAPI 3.1 schema for ChatGPT
├── test_connection.py    # Diagnostic script to test Odoo XML-RPC connection
└── README.md             # Documentation and deployment guide
```

---

## 🚀 Quickstart & Local Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Edit `.env` (or copy from `.env.example`) and provide your OneScreen Odoo email:
```env
ODOO_URL=https://erp.onescreenlatam.com
ODOO_DB=claryicon-master-7426961
ODOO_USERNAME=your.email@onescreenlatam.com
ODOO_API_KEY=9f2da2949576a5cdf548303c43aa7a85884c8c95
GPT_SECRET_TOKEN=Colombia_Flow_2026
ODOO_RMA_MODEL=rma.form
```

### 3. Verify Connection to Odoo
Run the diagnostic script to verify XML-RPC authentication and test basic reads:
```bash
python test_connection.py
```

### 4. Start the Middleware Server
```bash
uvicorn main:app --reload --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- OpenAPI Specification: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 🌐 Cloud Deployment (Render / Heroku)

### Deploying to Render
1. Push this directory to a GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Flow ERP Odoo middleware"
   git remote add origin https://github.com/<your-user>/<your-repo>.git
   git branch -M main
   git push -u origin main
   ```
2. Log into [Render Dashboard](https://dashboard.render.com/) and click **New > Web Service**.
3. Connect your GitHub repository.
4. Configure service settings:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. In the **Environment Variables** tab, add:
   - `ODOO_URL`: `https://erp.onescreenlatam.com`
   - `ODOO_DB`: `claryicon-master-7426961`
   - `ODOO_USERNAME`: `your.email@onescreenlatam.com`
   - `ODOO_API_KEY`: `9f2da2949576a5cdf548303c43aa7a85884c8c95`
   - `GPT_SECRET_TOKEN`: `Colombia_Flow_2026` (or your chosen secure token)
6. Deploy! Render will provide a public URL like `https://flow-odoo-middleware.onrender.com`.

---

## 🤖 ChatGPT Custom Action Setup

To connect ChatGPT to your middleware:

1. Open **ChatGPT** -> **Explore GPTs** -> **Create a GPT** (or edit your existing Custom GPT).
2. In the **Configure** tab:
   - Name: `OneScreen Colombia Supply Chain Assistant`
   - Description: `Queries open Purchase Orders, overdue activities, and RMAs from Odoo ERP.`
3. Scroll down to **Actions** and click **Create new action**.
4. In the **Schema** box:
   - Paste the contents of `openapi.json` from this repository, OR
   - Enter your public OpenAPI URL (e.g. `https://<your-render-app>.onrender.com/openapi.json`) and click **Import**.
5. Set up **Authentication**:
   - Authentication Type: **API Key**
   - Auth Type: **Bearer**
   - API Key: Enter your `GPT_SECRET_TOKEN` (e.g., `Colombia_Flow_2026`).
6. Test in the preview pane by prompting:
   - *"What Colombia purchase orders are currently open?"*
   - *"Check if there are any overdue supply chain activities."*
   - *"Show me details for Purchase Order P00012."*

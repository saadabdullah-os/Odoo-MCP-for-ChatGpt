"""
Test script to verify Odoo XML-RPC connection, credentials, and RMA models.
Usage:
    python test_connection.py
"""
import os
import xmlrpc.client
from dotenv import load_dotenv

load_dotenv()

ODOO_URL = os.environ.get("ODOO_URL", "https://erp.onescreenlatam.com")
ODOO_DB = os.environ.get("ODOO_DB", "claryicon-master-7426961")
ODOO_USERNAME = os.environ.get("ODOO_USERNAME")
ODOO_API_KEY = os.environ.get("ODOO_API_KEY", "9f2da2949576a5cdf548303c43aa7a85884c8c95")

CANDIDATE_RMA_MODELS = [
    'rma.form',
    'rma.request',
    'x_rma',
    'rma.rma',
    'rma',
    'rma_form',
    'rma.order',
    'return.order',
    'rma.ticket',
    'x_rma_form',
    'rma_from_forms'
]

def test():
    print(f"Connecting to Odoo at: {ODOO_URL}")
    print(f"Database: {ODOO_DB}")
    print(f"Username: {ODOO_USERNAME or '[NOT SET in .env!]'}")

    if not ODOO_USERNAME:
        print("\n[ERROR] ODOO_USERNAME is not set. Please add your email to .env file.")
        return

    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common', allow_none=True)
        version_info = common.version()
        print(f"Server version: {version_info.get('server_version', 'Unknown')}")

        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_API_KEY, {})
        if not uid:
            print("[ERROR] Authentication failed. Check your ODOO_USERNAME and ODOO_API_KEY.")
            return

        print(f"[SUCCESS] Authenticated successfully! User ID (UID): {uid}")

        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object', allow_none=True)

        # 1. Test Purchase Orders count
        po_count = models.execute_kw(ODOO_DB, uid, ODOO_API_KEY, 'purchase.order', 'search_count', [[]])
        print(f"Total Purchase Orders in DB: {po_count}")

        # 2. Test Activities count
        activity_count = models.execute_kw(ODOO_DB, uid, ODOO_API_KEY, 'mail.activity', 'search_count', [[]])
        print(f"Total Activities in DB: {activity_count}")

        # 3. Test RMA Models directly
        print("\nProbing candidate RMA technical models directly...")
        matched_model = None
        for candidate in CANDIDATE_RMA_MODELS:
            try:
                count = models.execute_kw(ODOO_DB, uid, ODOO_API_KEY, candidate, 'search_count', [[]])
                print(f"  --> FOUND! Model '{candidate}' exists and accessible! Total records: {count}")
                matched_model = candidate
                
                # Fetch available fields on this model
                fields_dict = models.execute_kw(ODOO_DB, uid, ODOO_API_KEY, candidate, 'fields_get', [], {'attributes': ['type', 'string']})
                key_fields = [k for k in fields_dict.keys() if any(sub in k.lower() for sub in ['name', 'state', 'partner', 'date', 'order', 'po', 'so', 'desc'])]
                print(f"      Key fields on {candidate}: {key_fields[:20]}")
                break
            except Exception:
                pass

        if not matched_model:
            print("  None of the standard RMA candidate names matched directly.")
            print("  You can ask your Odoo Admin for the exact technical model name used by 'rma_from_forms',")
            print("  or set ODOO_RMA_MODEL in your .env file.")

    except Exception as e:
        print(f"\n[EXCEPTION] Error communicating with Odoo: {e}")

if __name__ == "__main__":
    test()

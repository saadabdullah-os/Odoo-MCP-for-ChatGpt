"""
Verification test suite for Flow ERP Odoo Middleware.
Tests live integration with Odoo and validates all endpoints.
"""
import os
import json
from fastapi.testclient import TestClient
from main import app, GPT_SECRET_TOKEN

client = TestClient(app)
headers = {"Authorization": f"Bearer {GPT_SECRET_TOKEN}"}

def run_tests():
    print("========================================")
    print(" RUNNING INTEGRATION TESTS FOR FLOW ERP ")
    print("========================================")

    # 1. Test Root
    res = client.get("/")
    print(f"\n1. GET / -> Status {res.status_code}")
    print("   Response:", res.json())
    assert res.status_code == 200

    # 2. Test Health
    res = client.get("/health")
    print(f"\n2. GET /health -> Status {res.status_code}")
    assert res.status_code == 200

    # 3. Test Security (Unauthorized)
    res = client.get("/activities/overdue")
    print(f"\n3. Security check (No Auth) -> Status {res.status_code} (Expected 401/403)")
    assert res.status_code in (401, 403)

    res = client.get("/activities/overdue", headers={"Authorization": "Bearer invalid_secret"})
    print(f"   Security check (Bad Token) -> Status {res.status_code} (Expected 403)")
    assert res.status_code == 403

    # 4. Test Overdue Activities
    res = client.get("/activities/overdue", headers=headers)
    print(f"\n4. GET /activities/overdue -> Status {res.status_code}")
    activities = res.json()
    print(f"   Found {len(activities)} overdue activities")
    if activities:
        print("   Sample:", activities[0])
    assert res.status_code == 200

    # 5. Test Open Purchase Orders
    res = client.get("/pos/open", headers=headers)
    print(f"\n5. GET /pos/open -> Status {res.status_code}")
    pos = res.json()
    print(f"   Found {len(pos)} open purchase orders")
    po_name = None
    if pos:
        po_name = pos[0]['name']
        print(f"   Sample PO: {po_name} | Vendor: {pos[0]['partner_id']} | Total: {pos[0]['amount_total']}")
    assert res.status_code == 200

    # 6. Test PO Details
    if po_name:
        res = client.get(f"/pos/{po_name}", headers=headers)
        print(f"\n6. GET /pos/{po_name} -> Status {res.status_code}")
        po_detail = res.json()
        print(f"   PO Lines count: {len(po_detail.get('order_lines_detail', []))}")
        if po_detail.get('order_lines_detail'):
            print("   Sample Line:", po_detail['order_lines_detail'][0])
        assert res.status_code == 200

    # 7. Test Open RMAs
    res = client.get("/rmas/open", headers=headers)
    print(f"\n7. GET /rmas/open -> Status {res.status_code}")
    rmas = res.json()
    print(f"   Found {len(rmas)} open RMAs")
    rma_name = None
    if rmas:
        rma_name = rmas[0]['name']
        print(f"   Sample RMA: {rma_name} | Customer: {rmas[0].get('customer_name') or rmas[0].get('partner_id')} | Stage: {rmas[0].get('stage_id')}")
    assert res.status_code == 200

    # 8. Test RMA Details
    if rma_name:
        res = client.get(f"/rmas/{rma_name}", headers=headers)
        print(f"\n8. GET /rmas/{rma_name} -> Status {res.status_code}")
        rma_detail = res.json()
        print(f"   Device: {rma_detail.get('device_model')} (S/N: {rma_detail.get('device_serial')})")
        print(f"   Failure: {rma_detail.get('failure_description')}")
        assert res.status_code == 200

    print("\n========================================")
    print(" ALL ENDPOINTS TESTED & PASSED 100%!   ")
    print("========================================")

if __name__ == "__main__":
    run_tests()

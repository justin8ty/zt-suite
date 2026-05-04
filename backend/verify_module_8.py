import httpx
import time
import sys
import random

BASE_URL = "http://127.0.0.1:8000/api"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"


def log(msg, status="INFO"):
    print(f"[{status}] {msg}")


def verify_module_8():
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    unique_id = int(time.time())
    user_email = f"net_admin_{unique_id}@example.com"
    user_password = "password123"
    hostname = f"server-{unique_id}"

    log("=== Starting Verification of Module 8 (Traffic + Alerts) ===")

    # 1. Register & Login as Admin (for viewing)
    log("1. Logging in as Admin")
    resp = client.post(
        "/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if resp.status_code != 200:
        log(f"   Login failed: {resp.text}", "FAIL")
        sys.exit(1)
    admin_token = resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    log("   Success: Admin logged in", "PASS")

    # 2. Register Device (by a normal user/agent)
    log("2. Registering Agent Device")
    client.post("/users", json={"email": user_email, "password": user_password})
    resp = client.post(
        "/auth/login", json={"email": user_email, "password": user_password}
    )
    user_token = resp.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    resp = client.post(
        "/devices",
        json={"hostname": hostname, "os_type": "linux", "os_version": "ubuntu 22.04"},
        headers=user_headers,
    )
    device_id = resp.json()["id"]
    log(f"   Success: Device registered (ID: {device_id})", "PASS")

    # 3. Ingest Traffic
    log("3. Ingesting Traffic Batch (10 records)")
    records = []
    for i in range(10):
        records.append(
            {
                "src_ip": f"192.168.1.{100 + i}",
                "dst_ip": "10.0.0.5",
                "src_port": random.randint(1024, 65535),
                "dst_port": 80,
                "protocol": "TCP",
                "bytes_sent": random.randint(100, 1000),
                "bytes_received": random.randint(100, 1000),
                "timestamp": "2024-01-26T12:00:00Z",  # Dummy time
            }
        )

    resp = client.post(
        "/traffic",
        json={"device_id": device_id, "records": records},
        headers=user_headers,
    )
    if resp.status_code == 201:
        log(f"   Success: Ingested {resp.json()['inserted']} records", "PASS")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")

    # 4. Report Alert
    log("4. Reporting Critical Anomaly Alert")
    alert_data = {
        "device_id": device_id,
        "severity": "critical",
        "category": "anomaly",
        "title": "Port Scanning Detected",
        "description": "Host performed sequential port scan on internal subnet.",
        "source_ip": "192.168.1.105",
    }
    resp = client.post("/alerts", json=alert_data, headers=user_headers)
    if resp.status_code == 201:
        alert_id = resp.json()["id"]
        log(f"   Success: Alert created (ID: {alert_id})", "PASS")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")
        sys.exit(1)

    # 5. List Traffic (as Admin)
    log("5. Listing Traffic (Admin)")
    resp = client.get(f"/traffic?device_id={device_id}", headers=admin_headers)
    if resp.status_code == 200:
        records = resp.json()
        log(f"   Success: Retrieved {len(records)} records", "PASS")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")

    # 6. List Alerts (as Admin)
    log("6. Listing Alerts (Admin)")
    resp = client.get("/alerts", headers=admin_headers)
    if resp.status_code == 200:
        alerts = resp.json()
        target_alert = next((a for a in alerts if a["id"] == alert_id), None)
        if target_alert:
            log("   Success: Found reported alert", "PASS")
        else:
            log("   Failed: Alert not found in list", "FAIL")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")

    # 7. Acknowledge Alert (as Admin)
    log("7. Acknowledging Alert")
    resp = client.patch(
        f"/alerts/{alert_id}", json={"is_acknowledged": True}, headers=admin_headers
    )
    if resp.status_code == 200:
        if resp.json()["is_acknowledged"]:
            log("   Success: Alert acknowledged", "PASS")
        else:
            log("   Failed: Status not updated", "FAIL")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")

    log("\n=== Verification Complete ===")


if __name__ == "__main__":
    try:
        verify_module_8()
    except Exception as e:
        log(f"Error executing verification: {e}", "ERROR")

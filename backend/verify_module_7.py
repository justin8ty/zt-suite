import httpx
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api"


def log(msg, status="INFO"):
    print(f"[{status}] {msg}")


def verify_module_7():
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    unique_id = int(time.time())
    user_email = f"device_owner_{unique_id}@example.com"
    user_password = "password123"
    hostname = f"laptop-{unique_id}"

    log("=== Starting Verification of Module 7 (Device Trust) ===")

    # 1. Register & Login
    log("1. Registering and Logging in User")
    client.post("/users", json={"email": user_email, "password": user_password})
    resp = client.post(
        "/auth/login", json={"email": user_email, "password": user_password}
    )
    if resp.status_code != 200:
        log(f"   Login failed: {resp.text}", "FAIL")
        sys.exit(1)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    log("   Success: User logged in", "PASS")

    # 2. Register Device
    log(f"2. Registering Device: {hostname}")
    device_data = {
        "hostname": hostname,
        "os_type": "windows",
        "os_version": "11.0",
        "agent_version": "1.0.0",
    }
    resp = client.post("/devices", json=device_data, headers=headers)
    if resp.status_code == 200:
        device = resp.json()
        device_id = device["id"]
        log(f"   Success: Device registered (ID: {device_id})", "PASS")
        if device["is_compliant"]:
            log("   Warning: Device compliant by default? Should be false.", "WARN")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")
        sys.exit(1)

    # 3. Submit Non-Compliant Posture
    log("3. Submitting Non-Compliant Posture (No Firewall, No AV)")
    bad_report = {
        "antivirus_present": False,
        "antivirus_enabled": False,
        "firewall_enabled": False,
        "disk_encrypted": True,
        "os_up_to_date": True,
    }
    resp = client.post(
        f"/devices/{device_id}/posture", json=bad_report, headers=headers
    )
    if resp.status_code == 200:
        report = resp.json()
        log(f"   Report Score: {report['compliance_score']}")
        if not report["is_compliant"]:
            log("   Success: Posture evaluated as Non-Compliant", "PASS")
        else:
            log("   Failed: Should be non-compliant", "FAIL")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")

    # 4. Verify Device Status
    log("4. Verifying Device Status is Non-Compliant")
    resp = client.get(f"/devices/{device_id}", headers=headers)
    if resp.json()["is_compliant"] is False:
        log("   Success: Device status updated to Non-Compliant", "PASS")
    else:
        log("   Failed: Device status not updated", "FAIL")

    # 5. Submit Compliant Posture
    log("5. Submitting Compliant Posture (All checks pass)")
    good_report = {
        "antivirus_present": True,
        "antivirus_enabled": True,
        "firewall_enabled": True,
        "disk_encrypted": True,
        "os_up_to_date": True,
    }
    resp = client.post(
        f"/devices/{device_id}/posture", json=good_report, headers=headers
    )
    if resp.status_code == 200:
        report = resp.json()
        log(f"   Report Score: {report['compliance_score']}")
        if report["is_compliant"]:
            log("   Success: Posture evaluated as Compliant", "PASS")
        else:
            log("   Failed: Should be compliant", "FAIL")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")

    # 6. Verify Device Status Updated
    log("6. Verifying Device Status is Compliant")
    resp = client.get(f"/devices/{device_id}", headers=headers)
    if resp.json()["is_compliant"] is True:
        log("   Success: Device status updated to Compliant", "PASS")
    else:
        log("   Failed: Device status not updated", "FAIL")

    log("\n=== Verification Complete ===")


if __name__ == "__main__":
    try:
        verify_module_7()
    except Exception as e:
        log(f"Error executing verification: {e}", "ERROR")

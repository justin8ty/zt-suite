import httpx
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"


def log(msg, status="INFO"):
    print(f"[{status}] {msg}")


def verify_module_6():
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    unique_id = int(time.time())
    user_email = f"logger_{unique_id}@example.com"
    user_password = "password123"

    log("=== Starting Verification of Module 6 (Access Logging) ===")

    # 1. Login as Admin
    log("1. Logging in as Admin")
    resp = client.post(
        "/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if resp.status_code != 200:
        log(f"   Failed: {resp.text}", "FAIL")
        sys.exit(1)
    admin_token = resp.json()["access_token"]
    log("   Success: Admin logged in", "PASS")

    # 2. Check logs for Admin Login
    log("2. Verifying Admin Login Log")
    resp = client.get("/logs", headers={"Authorization": f"Bearer {admin_token}"})
    if resp.status_code == 200:
        logs = resp.json()["logs"]
        login_events = [
            l for l in logs if l["action"] == "login_success" and l["user_id"] == 1
        ]  # Admin ID is 1
        if login_events:
            log(f"   Success: Found {len(login_events)} login events for admin", "PASS")
        else:
            log("   Failed: No login event found for admin", "FAIL")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")

    # 3. Create Normal User
    log("3. Registering Normal User")
    resp = client.post("/users", json={"email": user_email, "password": user_password})
    user_id = resp.json()["id"]

    # 4. Login Normal User
    log("4. Logging in as Normal User")
    resp = client.post(
        "/auth/login", json={"email": user_email, "password": user_password}
    )
    user_token = resp.json()["access_token"]
    log("   Success: User logged in", "PASS")

    # 5. Fail Access (RBAC)
    log("5. Attempting Admin Access as Normal User (Should Fail)")
    resp = client.get("/logs", headers={"Authorization": f"Bearer {user_token}"})
    if resp.status_code == 403:
        log("   Success: Access Denied (403)", "PASS")
    else:
        log(f"   Failed: Expected 403, got {resp.status_code}", "FAIL")

    # 6. Verify Log of Failure (as Admin)
    log("6. Verifying Access Denied Log (as Admin)")
    resp = client.get("/logs", headers={"Authorization": f"Bearer {admin_token}"})
    if resp.status_code == 200:
        logs = resp.json()["logs"]
        # Look for most recent failure
        denial_events = [
            l
            for l in logs
            if l["action"] == "access_denied_role" and l["user_id"] == user_id
        ]
        if denial_events:
            log(
                f"   Success: Found {len(denial_events)} denial events for user {user_id}",
                "PASS",
            )
            log(f"   Latest Detail: {denial_events[0]['details']}")
        else:
            log(f"   Failed: No denial event found for user {user_id}", "FAIL")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")

    log("\n=== Verification Complete ===")


if __name__ == "__main__":
    try:
        verify_module_6()
    except Exception as e:
        log(f"Error executing verification: {e}", "ERROR")

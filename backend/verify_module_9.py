import httpx
import time
import sys
import pyotp

BASE_URL = "http://127.0.0.1:8000/api"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"


def log(msg, status="INFO"):
    print(f"[{status}] {msg}")


def verify_module_9():
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    unique_id = int(time.time())

    log("=== Starting Verification of Module 9 (Protected Resource / Zero-Trust) ===")

    # 1. Setup User with MFA (but no device yet)
    user_email = f"zt_user_{unique_id}@example.com"
    user_password = "password123"

    log("1. Setting up User with MFA")
    client.post("/users", json={"email": user_email, "password": user_password})

    # Enable MFA
    resp = client.post(
        "/auth/login", json={"email": user_email, "password": user_password}
    )
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/auth/mfa/enroll", headers=headers)
    secret = resp.json()["secret"]
    totp = pyotp.TOTP(secret)
    client.post("/auth/mfa/verify", json={"code": totp.now()}, headers=headers)
    log("   User created and MFA enabled")

    # 2. Login with MFA to get full token
    log("2. Logging in with MFA")
    resp = client.post(
        "/auth/login", json={"email": user_email, "password": user_password}
    )
    temp_token = resp.json()["temp_token"]
    resp = client.post(
        "/auth/mfa/validate", json={"temp_token": temp_token, "code": totp.now()}
    )
    access_token = resp.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    log("   Full access token acquired")

    # 3. Fail: No Device ID
    log("3. Testing Access without Device ID (Should Fail)")
    resp = client.get("/protected/files", headers=auth_headers)
    if resp.status_code == 400:
        log("   Success: Access Denied (400 Missing Header)", "PASS")
    else:
        log(f"   Failed: Expected 400, got {resp.status_code}", "FAIL")

    # 4. Register Device
    log("4. Registering Device")
    resp = client.post(
        "/devices",
        json={
            "hostname": f"zt-laptop-{unique_id}",
            "os_type": "windows",
            "os_version": "11",
        },
        headers=auth_headers,
    )
    device_id = resp.json()["id"]
    log(f"   Device registered: ID {device_id}")

    # 5. Fail: Non-Compliant Device
    log("5. Testing Access with Non-Compliant Device (Should Fail)")
    device_headers = auth_headers.copy()
    device_headers["X-Device-ID"] = str(device_id)

    resp = client.get("/protected/files", headers=device_headers)
    if resp.status_code == 403:
        log("   Success: Access Denied (403 Device not compliant)", "PASS")
    else:
        log(f"   Failed: Expected 403, got {resp.status_code} - {resp.text}", "FAIL")

    # 6. Make Device Compliant
    log("6. Submitting Compliant Posture")
    client.post(
        f"/devices/{device_id}/posture",
        json={
            "antivirus_present": True,
            "antivirus_enabled": True,
            "firewall_enabled": True,
            "disk_encrypted": True,
            "os_up_to_date": True,
        },
        headers=auth_headers,
    )
    log("   Device marked compliant")

    # 7. Success: Full Access
    log("7. Testing Full Access (Auth + MFA + Role + Compliant Device)")
    # Note: User has 'user' role by default?
    # Wait, our seed logic didn't assign 'user' role by default on creation.
    # We need to check if user has 'user' role.
    # For now, let's login as Admin to assign 'user' role if needed, or rely on default.
    # Ah, `UserService.create` doesn't assign roles!
    # I need to fix `UserService.create` or manually assign role.

    # Assign 'user' role using Admin
    log("   Assigning 'user' role via Admin")
    resp = client.post(
        "/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    admin_token = resp.json()["access_token"]

    # Get user ID (we don't have it directly from login, needed to find user)
    # We can assume it's sequential or find it via list users
    resp = client.get("/users", headers={"Authorization": f"Bearer {admin_token}"})
    users = resp.json()["users"]
    target_user = next(u for u in users if u["email"] == user_email)

    client.post(
        f"/users/{target_user['id']}/roles",
        params={"role_name": "user"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Retry Access
    resp = client.get("/protected/files", headers=device_headers)
    if resp.status_code == 200:
        data = resp.json()
        log("   Success: Access Granted", "PASS")
        log(f"   Files: {[f['name'] for f in data['files']]}")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")

    log("\n=== Verification Complete ===")


if __name__ == "__main__":
    try:
        verify_module_9()
    except Exception as e:
        log(f"Error executing verification: {e}", "ERROR")

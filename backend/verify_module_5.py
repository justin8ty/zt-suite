import httpx
import time
import sys
import pyotp

BASE_URL = "http://127.0.0.1:8000/api"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"


def log(msg, status="INFO"):
    print(f"[{status}] {msg}")


def verify_module_5():
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    unique_id = int(time.time())
    user_email = f"mfa_user_{unique_id}@example.com"
    user_password = "password123"

    log("=== Starting Verification of Module 5 (MFA) ===")

    # 1. Create User
    log(f"1. Registering new user: {user_email}")
    resp = client.post("/users", json={"email": user_email, "password": user_password})
    if resp.status_code == 201:
        log("   Success: User created", "PASS")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")
        sys.exit(1)

    # 2. Login (MFA Disabled)
    log("2. Logging in (MFA Disabled)")
    resp = client.post(
        "/auth/login", json={"email": user_email, "password": user_password}
    )
    if resp.status_code == 200:
        data = resp.json()
        if "access_token" in data:
            access_token = data["access_token"]
            log("   Success: Received Access Token (MFA not enforced)", "PASS")
        else:
            log(f"   Failed: Unexpected response: {data}", "FAIL")
            sys.exit(1)
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")
        sys.exit(1)

    # 3. Enroll MFA
    log("3. Enrolling in MFA")
    resp = client.post(
        "/auth/mfa/enroll", headers={"Authorization": f"Bearer {access_token}"}
    )
    if resp.status_code == 200:
        mfa_data = resp.json()
        secret = mfa_data["secret"]
        uri = mfa_data["provisioning_uri"]
        log(f"   Success: Received Secret: {secret[:5]}... and URI", "PASS")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")
        sys.exit(1)

    # 4. Verify MFA
    log("4. Verifying MFA (Enabling)")
    totp = pyotp.TOTP(secret)
    code = totp.now()
    log(f"   Generated Code: {code}")

    resp = client.post(
        "/auth/mfa/verify",
        json={"code": code},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if resp.status_code == 200:
        log("   Success: MFA Enabled", "PASS")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")
        sys.exit(1)

    # 5. Login (MFA Enabled)
    log("5. Logging in (MFA Enabled)")
    resp = client.post(
        "/auth/login", json={"email": user_email, "password": user_password}
    )
    if resp.status_code == 200:
        data = resp.json()
        if data.get("mfa_required") is True:
            temp_token = data["temp_token"]
            log("   Success: Received MFA Challenge (temp_token)", "PASS")
        else:
            log(f"   Failed: Did not receive MFA challenge. Got: {data.keys()}", "FAIL")
            sys.exit(1)
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")
        sys.exit(1)

    # 6. Validate MFA Login
    log("6. Validating MFA Login")
    code = totp.now()
    resp = client.post(
        "/auth/mfa/validate", json={"temp_token": temp_token, "code": code}
    )
    if resp.status_code == 200:
        tokens = resp.json()
        if "access_token" in tokens:
            log("   Success: Received Final Access Token", "PASS")
        else:
            log(f"   Failed: Unexpected response: {tokens}", "FAIL")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")

    log("\n=== Verification Complete ===")


if __name__ == "__main__":
    try:
        verify_module_5()
    except Exception as e:
        log(f"Error executing verification: {e}", "ERROR")

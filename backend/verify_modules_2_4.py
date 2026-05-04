import httpx
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"


def log(msg, status="INFO"):
    print(f"[{status}] {msg}")


def verify_modules():
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    unique_id = int(time.time())
    user_email = f"testuser_{unique_id}@example.com"
    user_password = "password123"

    log("=== Starting Verification of Modules 2, 3, 4 ===")

    # --- Module 2: User Management ---
    log("\n--- Module 2: User Management ---")

    # 1. Create User
    log(f"1. Registering new user: {user_email}")
    resp = client.post("/users", json={"email": user_email, "password": user_password})
    if resp.status_code == 201:
        user_data = resp.json()
        log(f"   Success: User created with ID {user_data['id']}", "PASS")
        user_id = user_data["id"]
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")
        sys.exit(1)

    # --- Module 3: Authentication ---
    log("\n--- Module 3: Authentication (JWT) ---")

    # 2. Login
    log("2. Logging in with new user credentials")
    resp = client.post(
        "/auth/login", json={"email": user_email, "password": user_password}
    )
    if resp.status_code == 200:
        tokens = resp.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        log("   Success: Received Access and Refresh tokens", "PASS")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")
        sys.exit(1)

    # 3. Refresh Token
    log("3. Refreshing access token")
    resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    if resp.status_code == 200:
        new_tokens = resp.json()
        new_access_token = new_tokens["access_token"]
        log("   Success: Token refreshed", "PASS")
        # Update current tokens
        access_token = new_access_token
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")

    # 4. Logout
    log("4. Logging out (Revoking refresh token)")
    resp = client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if resp.status_code == 204:
        log("   Success: Logout successful", "PASS")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")

    # 5. Verify Revocation
    log("5. Verifying token revocation (trying refresh again)")
    resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    if resp.status_code == 401:
        log("   Success: Revoked token rejected (401)", "PASS")
    else:
        log(f"   Failed: Expected 401, got {resp.status_code}", "FAIL")

    # --- Module 4: RBAC ---
    log("\n--- Module 4: RBAC (Roles & Permissions) ---")

    # 6. Login as Admin
    log("6. Logging in as Admin (System Bootstrap Check)")
    resp = client.post(
        "/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if resp.status_code == 200:
        admin_token = resp.json()["access_token"]
        log("   Success: Admin logged in", "PASS")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")
        sys.exit(1)

    # 7. Admin Action (List Users)
    log("7. Testing Admin permission: List Users")
    resp = client.get("/users", headers={"Authorization": f"Bearer {admin_token}"})
    if resp.status_code == 200:
        count = resp.json()["total"]
        log(f"   Success: Admin can list users (Total: {count})", "PASS")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")

    # 8. User Action (List Users) - Should Fail
    # Note: We need a valid user token again since we logged out the previous one
    # Let's login the user again
    resp = client.post(
        "/auth/login", json={"email": user_email, "password": user_password}
    )
    user_token = resp.json()["access_token"]

    log("8. Testing Restricted permission: Normal User listing users")
    resp = client.get("/users", headers={"Authorization": f"Bearer {user_token}"})
    if resp.status_code == 403:
        log("   Success: Normal user denied access (403 Forbidden)", "PASS")
    else:
        log(f"   Failed: Expected 403, got {resp.status_code}", "FAIL")

    # 9. Assign Role
    log(f"9. Admin assigning 'viewer' role to User ID {user_id}")
    resp = client.post(
        f"/users/{user_id}/roles",
        params={"role_name": "viewer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    if resp.status_code == 200:
        roles = [r["name"] for r in resp.json()["roles"]]
        if "viewer" in roles:
            log(f"   Success: Role assigned. Current roles: {roles}", "PASS")
        else:
            log(f"   Failed: Response did not contain new role. Roles: {roles}", "FAIL")
    else:
        log(f"   Failed: {resp.status_code} - {resp.text}", "FAIL")

    log("\n=== Verification Complete ===")


if __name__ == "__main__":
    try:
        verify_modules()
    except Exception as e:
        log(f"Error executing verification: {e}", "ERROR")

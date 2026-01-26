import httpx
import time

BASE_URL = "http://127.0.0.1:8000/api"


def test_rbac_flow():
    # 1. Login as Admin (auto-seeded)
    print("1. Logging in as Admin...")
    resp = httpx.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return

    admin_tokens = resp.json()
    admin_access = admin_tokens["access_token"]
    print("   Admin Login success!")

    # 2. Access Admin-only endpoint (List Users)
    print("\n2. Accessing Admin-only endpoint...")
    resp = httpx.get(
        f"{BASE_URL}/users", headers={"Authorization": f"Bearer {admin_access}"}
    )
    if resp.status_code == 200:
        users = resp.json()["users"]
        print(f"   Success! Found {len(users)} users.")
        for u in users:
            print(f"   - {u['email']} (Roles: {[r['name'] for r in u['roles']]})")
    else:
        print(f"   Failure: {resp.status_code} - {resp.text}")

    # 3. Create a normal user (public endpoint)
    print("\n3. Creating normal user...")
    user_email = f"user_{int(time.time())}@example.com"
    resp = httpx.post(
        f"{BASE_URL}/users", json={"email": user_email, "password": "password123"}
    )
    if resp.status_code != 201:
        print(f"   User creation failed: {resp.text}")
        # If user exists from previous run, try to login
    else:
        print("   User created successfully.")

    # 4. Login as normal user
    print("\n4. Logging in as Normal User...")
    resp = httpx.post(
        f"{BASE_URL}/auth/login", json={"email": user_email, "password": "password123"}
    )
    if resp.status_code != 200:
        print(f"   Login failed: {resp.text}")
        return

    user_tokens = resp.json()
    user_access = user_tokens["access_token"]

    # 5. Access Admin-only endpoint as User (Should Fail)
    print("\n5. Accessing Admin-only endpoint as User...")
    resp = httpx.get(
        f"{BASE_URL}/users", headers={"Authorization": f"Bearer {user_access}"}
    )
    if resp.status_code == 403:
        print("   Success: Access Forbidden (403) as expected.")
    else:
        print(f"   Failure: Access allowed! Status: {resp.status_code}")

    # 6. Assign role (Admin operation)
    print("\n6. Assigning VIEWER role to user (as Admin)...")
    user_id = httpx.get(
        f"{BASE_URL}/users/{user_email}",
        headers={"Authorization": f"Bearer {admin_access}"},
    )
    # Wait, we don't have get_by_email endpoint, only by ID.
    # We can find ID from step 2 list or from create response.
    # Let's use list users to find the new user ID.
    resp = httpx.get(
        f"{BASE_URL}/users", headers={"Authorization": f"Bearer {admin_access}"}
    )
    users = resp.json()["users"]
    target_user = next((u for u in users if u["email"] == user_email), None)

    if target_user:
        resp = httpx.post(
            f"{BASE_URL}/users/{target_user['id']}/roles",
            params={"role_name": "viewer"},
            headers={"Authorization": f"Bearer {admin_access}"},
        )
        if resp.status_code == 200:
            print("   Success: Role assigned.")
            print(f"   New roles: {[r['name'] for r in resp.json()['roles']]}")
        else:
            print(f"   Failure: {resp.status_code} - {resp.text}")
    else:
        print("   Could not find user to assign role.")


if __name__ == "__main__":
    try:
        test_rbac_flow()
    except Exception as e:
        print(f"Error: {e}")

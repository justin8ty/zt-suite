import httpx
import time

BASE_URL = "http://127.0.0.1:8000/api"


def test_auth_flow():
    # 1. Login
    print("1. Logging in...")
    resp = httpx.post(
        f"{BASE_URL}/auth/login",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return

    tokens = resp.json()
    print("   Login success!")
    print(f"   Access Token: {tokens['access_token'][:20]}...")
    print(f"   Refresh Token: {tokens['refresh_token'][:20]}...")

    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 2. Refresh Token
    print("\n2. Refreshing token...")
    resp = httpx.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": refresh_token})
    if resp.status_code != 200:
        print(f"Refresh failed: {resp.text}")
        return

    new_tokens = resp.json()
    print("   Refresh success!")
    print(f"   New Access Token: {new_tokens['access_token'][:20]}...")

    # 3. Logout
    print("\n3. Logging out...")
    resp = httpx.post(
        f"{BASE_URL}/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if resp.status_code != 204:
        print(f"Logout failed: {resp.text}")
        return
    print("   Logout success!")

    # 4. Try refresh again (should fail)
    print("\n4. Verifying token revocation...")
    resp = httpx.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": refresh_token})
    if resp.status_code == 401:
        print("   Success: Revoked token rejected.")
    else:
        print(f"   Failure: Revoked token accepted! Status: {resp.status_code}")


if __name__ == "__main__":
    try:
        test_auth_flow()
    except Exception as e:
        print(f"Error: {e}")

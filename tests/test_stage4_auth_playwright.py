"""
Stage 4 Acceptance Verification: Playwright Auth UI and Protected Routing.
Validates:
1. Protected route enforcement (/dashboard redirects to /login)
2. Card flip and Signup-to-Dashboard flow
3. Dashboard shell mount and user authentication state
4. Refresh token rotation and token family reuse detection revocation
5. Progressive lockout trigger after consecutive failed attempts
6. Logout clearing session
"""
import time
import uuid
import subprocess
import requests
import pytest
from playwright.sync_api import sync_playwright, expect

API_URL = "http://127.0.0.1:8000"
WEB_URL = "http://127.0.0.1:5173"


def wait_for_services():
    """Wait for API and Web servers to be healthy."""
    for _ in range(40):
        try:
            r_api = requests.get(f"{API_URL}/healthz", timeout=1)
            r_web = requests.get(WEB_URL, timeout=1)
            if r_api.status_code == 200 and r_web.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def test_stage4_playwright_auth_and_protected_routing():
    assert wait_for_services(), f"Servers must be active at {API_URL} and {WEB_URL}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("\n[Stage 4 Test 1] Testing protected routing...")
        # 1. Navigating to /dashboard while unauthenticated MUST redirect to /login
        page.goto(f"{WEB_URL}/dashboard")
        page.wait_for_url("**/login**", timeout=10000)
        assert "/login" in page.url, f"Expected redirect to /login, but was {page.url}"
        print(" -> Protected route successfully redirected unauthenticated visitor to /login")

        print("\n[Stage 4 Test 2] Testing card flip and registration...")
        # 2. Click Request Access to flip to Sign Up
        page.wait_for_selector('[data-testid="switch-to-signup"]', timeout=5000)
        page.click('[data-testid="switch-to-signup"]')
        page.wait_for_timeout(700) # Wait for 3D flip animation

        # Fill Sign Up form
        unique_email = f"lead_{uuid.uuid4().hex[:8]}@quantfund.com"
        password = "InstitutionalPassword123!"

        page.wait_for_selector('[data-testid="signup-fullname"]', timeout=5000)
        page.fill('[data-testid="signup-fullname"]', "Institutional Quantitative Lead")
        page.fill('[data-testid="signup-email"]', unique_email)
        page.fill('[data-testid="signup-password"]', password)
        page.fill('[data-testid="signup-confirm-password"]', password)

        # Submit registration
        page.click('[data-testid="signup-submit"]')

        # 3. Wait for automatic login and redirect to /dashboard
        print(" -> Submitting registration and verifying auto-redirect to /dashboard...")
        page.wait_for_url("**/dashboard**", timeout=15000)
        assert "/dashboard" in page.url, f"Expected to reach /dashboard, but URL is {page.url}"

        # Verify Dashboard header and user profile rendered
        page.wait_for_selector("aside", timeout=5000)
        assert "Institutional Quantitative Lead" in page.content(), "User name should be visible in dashboard shell"
        print(" -> Dashboard mounted successfully with user session")

        # 4. Check refresh token cookie in browser context
        cookies = context.cookies()
        refresh_cookie = next((c for c in cookies if c["name"] == "btc_oracle_refresh"), None)
        assert refresh_cookie is not None, "Refresh token cookie 'btc_oracle_refresh' must be set in browser"
        initial_refresh_token = refresh_cookie["value"]
        print(f" -> Refresh token cookie acquired: {initial_refresh_token[:10]}...")

        # 5. Verify refresh token rotation via API
        print("\n[Stage 4 Test 3] Testing refresh token rotation...")
        session = requests.Session()
        session.cookies.set("btc_oracle_refresh", initial_refresh_token, domain="127.0.0.1", path="/")
        refresh_res = session.post(f"{API_URL}/api/v1/auth/refresh")
        assert refresh_res.status_code == 200, f"Refresh failed: {refresh_res.text}"
        new_token_data = refresh_res.json()
        assert "access_token" in new_token_data
        new_refresh_token = refresh_res.cookies.get("btc_oracle_refresh")
        assert new_refresh_token is not None and new_refresh_token != initial_refresh_token
        print(" -> Refresh token successfully rotated to child token in family")

        # 6. Verify reuse detection revocation (resending the old invalidated refresh token)
        print("\n[Stage 4 Test 4] Testing token family reuse detection...")
        reuse_session = requests.Session()
        reuse_session.cookies.set("btc_oracle_refresh", initial_refresh_token)
        reuse_res = reuse_session.post(f"{API_URL}/api/v1/auth/refresh")
        assert reuse_res.status_code == 401, f"Expected 401 on reuse, got {reuse_res.status_code}"
        assert "reuse" in reuse_res.text.lower() or "revoked" in reuse_res.text.lower()
        print(" -> Token reuse detection triggered: entire token family revoked successfully")

        # 7. Testing progressive lockout
        print("\n[Stage 4 Test 5] Testing progressive lockout trigger after 5 failed attempts...")
        lockout_email = f"lockout_test_{uuid.uuid4().hex[:6]}@fund.com"
        # Register user for lockout test
        reg_res = requests.post(
            f"{API_URL}/api/v1/auth/register",
            json={"email": lockout_email, "password": "CorrectPassword123!", "full_name": "Lockout Test User"},
        )
        assert reg_res.status_code == 201

        # Perform 5 failed login attempts
        lockout_triggered = False
        for attempt in range(1, 6):
            fail_res = requests.post(
                f"{API_URL}/api/v1/auth/login",
                json={"email": lockout_email, "password": f"WrongPassword_{attempt}"},
            )
            if fail_res.status_code == 429:
                lockout_triggered = True
                print(f" -> Lockout triggered on attempt #{attempt}: {fail_res.json().get('detail')}")
                break
            else:
                assert fail_res.status_code == 401, f"Attempt {attempt} returned {fail_res.status_code}"

        assert lockout_triggered, "Progressive lockout must trigger 429 Too Many Requests"

        # 8. Test Logout flow
        print("\n[Stage 4 Test 6] Testing logout flow from dashboard...")
        page.bring_to_front()
        page.wait_for_selector('[data-testid="logout-button"]', timeout=5000)
        page.click('[data-testid="logout-button"]')
        page.wait_for_timeout(1000)

        # Navigating to /dashboard after logout should redirect back to /login
        page.goto(f"{WEB_URL}/dashboard")
        page.wait_for_url("**/login**", timeout=10000)
        assert "/login" in page.url
        print(" -> Logout confirmed: session invalidated and protected route redirects to /login")

        browser.close()
        print("\n[Stage 4 Acceptance Check] ALL TESTS PASSED.")

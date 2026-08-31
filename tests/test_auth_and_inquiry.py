"""Unit and integration tests for Real-Time Email & Mobile OTP Authentication and Inquiries."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app, otp_store

client = TestClient(app)


def test_send_and_verify_email_otp():
    test_email = "admin@zytrex.ai"
    
    # 1. Send OTP
    send_res = client.post("/api/auth/otp/send", json={"identifier": test_email})
    assert send_res.status_code == 200
    data = send_res.json()
    assert data["status"] == "success"
    assert data["channel"] == "email"
    dev_code = data["dev_code"]
    assert len(dev_code) == 6

    # 2. Verify with invalid OTP
    bad_res = client.post("/api/auth/otp/verify", json={"identifier": test_email, "code": "000000"})
    assert bad_res.status_code == 400

    # 3. Verify with correct OTP
    verify_res = client.post("/api/auth/otp/verify", json={"identifier": test_email, "code": dev_code})
    assert verify_res.status_code == 200
    auth_data = verify_res.json()
    assert auth_data["status"] == "authenticated"
    token = auth_data["token"]
    assert token.startswith("zytrex_sess_")

    # 4. Check /api/auth/me with session token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["authenticated"] is True
    assert me_res.json()["user"]["identifier"] == test_email

    # 5. Logout
    logout_res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200

    # 6. Check /api/auth/me after logout
    me_after = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_after.json()["authenticated"] is False


def test_send_mobile_otp():
    mobile = "+919876543210"
    res = client.post("/api/auth/otp/send", json={"identifier": mobile})
    assert res.status_code == 200
    data = res.json()
    assert data["channel"] == "mobile"
    assert len(data["dev_code"]) == 6


def test_contact_inquiry_submission():
    payload = {
        "full_name": "Alex Morgan",
        "email": "alex.morgan@techcorp.io",
        "phone": "+1 555 019 2834",
        "service_interest": "Software Modernization",
        "message": "We need our core dashboard modernized with high performance.",
    }
    res = client.post("/api/contact/inquiry", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert "Alex Morgan" in res.json()["message"]

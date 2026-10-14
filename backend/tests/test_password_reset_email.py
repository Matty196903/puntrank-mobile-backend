# Password reset email: template guardrails, delivery, reset flow, enumeration safety
import os
import sys
import uuid
import asyncio
import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
ORIGIN = BASE_URL
mongo = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
sys.path.insert(0, "/app/backend")


# Guardrails: build template the same way server does and run _assert_safe_email
def test_template_passes_guardrails():
    import server
    import email_service
    from unittest.mock import AsyncMock, patch
    captured = {}

    async def fake_send(**kw):
        captured.update(kw)
        email_service._assert_safe_email(kw["subject"], kw["html"])
        return "x"

    class FakeColl:
        async def find_one(self, *a, **k):
            return {"id": "u1", "email": "a@b.com", "name": "Jo <b>Smith</b>"}
        async def insert_one(self, *a, **k):
            return None

    class FakeDB:
        users = FakeColl()
        password_reset_tokens = FakeColl()

    with patch.object(server, "db", FakeDB()), patch.object(email_service, "send_email", side_effect=fake_send):
        body = server.ForgotPasswordInput(email="a@b.com", origin_url=ORIGIN)
        res = asyncio.get_event_loop().run_until_complete(server.forgot_password(body)) if False else asyncio.run(server.forgot_password(body))
    assert res["ok"] is True
    html = captured["html"]
    assert f"{ORIGIN}/reset-password?token=" in html
    assert "<form" not in html.lower()
    assert "&lt;b&gt;" not in html or "Jo," in html  # first name only, escaped
    assert "Set a new password" in html
    assert "#0A0D0E" in html and "#10B981" in html
    assert "1800 858 858" in html


class TestForgotPassword:
    def test_registered_deliverable(self):
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                          json={"email": "delivered@resend.dev", "origin_url": ORIGIN}, timeout=60)
        assert r.status_code == 200
        assert "reset link has been sent" in r.json()["message"]

    def test_nonexistent_email_generic(self):
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                          json={"email": f"nobody_{uuid.uuid4().hex[:6]}@nowhere.com", "origin_url": ORIGIN}, timeout=60)
        assert r.status_code == 200
        assert r.json()["message"] == "If an account exists for that email, a reset link has been sent."

    def test_bad_origin_rejected(self):
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                          json={"email": "delivered@resend.dev", "origin_url": "https://evil.com"}, timeout=30)
        assert r.status_code == 400


@pytest.fixture(scope="module")
def undeliverable_user():
    email = f"test_reset_{uuid.uuid4().hex[:6]}@puntrank.com.au"
    r = requests.post(f"{BASE_URL}/api/auth/register",
                      json={"email": email, "password": "oldpass123", "name": "Test Resetter"}, timeout=30)
    assert r.status_code == 200
    yield email
    uid = mongo.users.find_one({"email": email})["id"]
    mongo.password_reset_tokens.delete_many({"user_id": uid})
    mongo.users.delete_one({"email": email})


class TestResetFlow:
    def test_undeliverable_and_full_reset(self, undeliverable_user):
        email = undeliverable_user
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                          json={"email": email, "origin_url": ORIGIN}, timeout=60)
        assert r.status_code == 200
        assert r.json()["ok"] is True
        uid = mongo.users.find_one({"email": email})["id"]
        rec = mongo.password_reset_tokens.find_one({"user_id": uid, "used": False}, sort=[("_id", -1)])
        assert rec is not None
        token = rec["token"]
        r = requests.post(f"{BASE_URL}/api/auth/reset-password", json={"token": token, "new_password": "newpass789"})
        assert r.status_code == 200, r.text
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "newpass789"})
        assert r.status_code == 200 and r.json()["access_token"]
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "oldpass123"})
        assert r.status_code == 401
        r = requests.post(f"{BASE_URL}/api/auth/reset-password", json={"token": token, "new_password": "another123"})
        assert r.status_code == 400

    def test_short_password_rejected(self):
        r = requests.post(f"{BASE_URL}/api/auth/reset-password", json={"token": "x", "new_password": "abc"})
        assert r.status_code == 422

    def test_invalid_token(self):
        r = requests.post(f"{BASE_URL}/api/auth/reset-password", json={"token": "bogus", "new_password": "abcdef"})
        assert r.status_code == 400

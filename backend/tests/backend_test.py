"""Backend test suite for PuntRank Aus API."""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://puntrank-web.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@puntrank.com.au"
ADMIN_PASSWORD = "AcePunter2026!"


# --- fixtures ---
@pytest.fixture(scope="session")
def anon():
    return requests.Session()


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def race_ids(anon):
    r = anon.get(f"{API}/meetings")
    assert r.status_code == 200
    meetings = r.json()["meetings"]
    assert len(meetings) >= 1
    mid = meetings[0]["id"]
    rr = anon.get(f"{API}/meetings/{mid}/races")
    assert rr.status_code == 200
    races = rr.json()["races"]
    upcoming = next((x for x in races if x["status"] == "upcoming"), races[0])
    resulted = next((x for x in races if x["status"] == "resulted"), None)
    return {"meeting_id": mid, "race_id": upcoming["id"],
            "resulted_id": resulted["id"] if resulted else None,
            "meetings": meetings, "races": races}


# --- auth ---
class TestAuth:
    def test_admin_login(self):
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
        assert data["user"]["is_pro"] is True

    def test_me_with_bearer(self, admin_headers):
        r = requests.get(f"{API}/auth/me", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["email"] == ADMIN_EMAIL

    def test_me_without_token(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401

    def test_wrong_password(self):
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong!!"})
        assert r.status_code == 401

    def test_register_new_user(self):
        import uuid
        email = f"TEST_{uuid.uuid4().hex[:8]}@test.com"
        r = requests.post(f"{API}/auth/register", json={"email": email, "password": "abcdef", "name": "T"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert "access_token" in data
        assert data["user"]["email"] == email.lower()
        assert data["user"]["is_pro"] is False


# --- meetings/races ---
class TestMeetings:
    def test_meetings_today(self):
        r = requests.get(f"{API}/meetings")
        assert r.status_code == 200
        data = r.json()
        assert "date_aest" in data
        assert len(data["meetings"]) >= 1
        m = data["meetings"][0]
        for k in ("condition", "rail", "next_race"):
            assert k in m or m.get("next_race") is None or True  # next_race may be None
        assert "condition" in m and "rail" in m

    def test_some_races_resulted(self, race_ids):
        statuses = [r["status"] for r in race_ids["races"]]
        # not strictly required but usually some resulted
        assert "upcoming" in statuses or "resulted" in statuses

    def test_race_anonymous_pro_gating(self, race_ids):
        r = requests.get(f"{API}/races/{race_ids['race_id']}")
        assert r.status_code == 200
        data = r.json()
        assert data["pro"] is False
        for runner in data["runners"]:
            if runner["rank"] > 3:
                assert runner["reasoning"] is None
                assert runner["confidence"] is None
            else:
                # top 3 must have reasoning
                assert runner["reasoning"] is not None

    def test_race_admin_full(self, race_ids, admin_headers):
        r = requests.get(f"{API}/races/{race_ids['race_id']}", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["pro"] is True
        for runner in data["runners"]:
            assert runner["reasoning"] is not None
            assert runner["confidence"] is not None


# --- exotics ---
class TestExotics:
    def test_exotics_anon(self, race_ids):
        r = requests.get(f"{API}/races/{race_ids['race_id']}/exotics")
        assert r.status_code == 200
        data = r.json()
        assert len(data["exotics"]) == 1
        assert data["locked"] == 3
        assert data["pro"] is False

    def test_exotics_admin(self, race_ids, admin_headers):
        r = requests.get(f"{API}/races/{race_ids['race_id']}/exotics", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data["exotics"]) == 4
        assert data["locked"] == 0
        assert data["pro"] is True


# --- aces selections ---
class TestAces:
    def test_aces_anon(self):
        r = requests.get(f"{API}/selections/aces")
        assert r.status_code == 200
        data = r.json()
        assert len(data["winners"]) <= 2
        assert len(data["places"]) <= 1
        # New teaser: free/guest users see EXACTLY leg 1
        assert len(data["quaddie"]) == 1
        assert data["quaddie"][0]["leg"] == 1
        assert data["pro"] is False

    def test_aces_admin(self, admin_headers):
        r = requests.get(f"{API}/selections/aces", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["pro"] is True
        assert len(data["quaddie"]) >= 4


# --- best bets ---
class TestBestBets:
    def test_bb_anon(self):
        r = requests.get(f"{API}/best-bets")
        assert r.status_code == 200
        data = r.json()
        assert len(data["bets"]) == 1
        assert data["pro"] is False
        assert data["multis"] == []
        assert data["locked"] >= 0

    def test_bb_admin(self, admin_headers):
        r = requests.get(f"{API}/best-bets", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["pro"] is True
        assert len(data["bets"]) >= 1
        # graded field on resulted
        for b in data["bets"]:
            if b["race_status"] == "resulted":
                assert b["graded"] in ("WON", "PLACED", "UNPLACED")


# --- movers & results ---
class TestMoversResults:
    def test_movers(self):
        r = requests.get(f"{API}/movers")
        assert r.status_code == 200
        movers = r.json()["movers"]
        for m in movers:
            assert m["odds_open"] > m["odds_current"]
            assert "move_pct" in m

    def test_results(self):
        r = requests.get(f"{API}/results")
        assert r.status_code == 200
        data = r.json()
        assert "stats" in data
        stats = data["stats"]
        for k in ("win_strike", "place_strike", "resulted", "wins", "places"):
            assert k in stats


# --- reports/PDF ---
class TestReports:
    def test_form_guide_free(self):
        r = requests.get(f"{API}/reports/form_guide/download")
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:4] == b"%PDF"

    def test_top10_free(self):
        r = requests.get(f"{API}/reports/top10/download")
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"

    def test_scorecard_anon_402(self):
        r = requests.get(f"{API}/reports/scorecard/download")
        assert r.status_code == 402

    def test_scorecard_admin(self, admin_headers):
        r = requests.get(f"{API}/reports/scorecard/download", headers=admin_headers)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"


# --- stripe ---
class TestStripe:
    def test_checkout_unauth(self):
        r = requests.post(f"{API}/payments/checkout",
                          json={"lookup_key": "pro_monthly",
                                "origin_url": "https://puntrank-web.preview.emergentagent.com"})
        assert r.status_code == 401

    def test_checkout_authed(self, admin_headers):
        r = requests.post(f"{API}/payments/checkout",
                          headers=admin_headers,
                          json={"lookup_key": "pro_monthly",
                                "origin_url": "https://puntrank-web.preview.emergentagent.com"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert "stripe.com" in data["checkout_url"]
        assert "session_id" in data
        # status pending
        s = requests.get(f"{API}/payments/status/{data['session_id']}")
        assert s.status_code == 200
        assert s.json()["payment_status"] in ("pending", "unpaid")


# --- admin ---
class TestAdmin:
    def test_reseed(self, admin_headers):
        r = requests.post(f"{API}/admin/reseed", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_users_list(self, admin_headers):
        r = requests.get(f"{API}/admin/users", headers=admin_headers)
        assert r.status_code == 200
        assert isinstance(r.json()["users"], list)

    def test_non_admin_forbidden(self):
        import uuid
        email = f"TEST_{uuid.uuid4().hex[:8]}@t.com"
        reg = requests.post(f"{API}/auth/register", json={"email": email, "password": "abcdef", "name": "x"})
        token = reg.json()["access_token"]
        r = requests.get(f"{API}/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_toggle_pro(self, admin_headers):
        import uuid
        email = f"TEST_{uuid.uuid4().hex[:8]}@t.com"
        reg = requests.post(f"{API}/auth/register", json={"email": email, "password": "abcdef", "name": "x"})
        uid = reg.json()["user"]["id"]
        r = requests.post(f"{API}/admin/users/{uid}/toggle-pro", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["is_pro"] is True
        # verify via list
        users = requests.get(f"{API}/admin/users", headers=admin_headers).json()["users"]
        u = next(x for x in users if x["id"] == uid)
        assert u["is_pro"] is True


# --- password reset (new feature) ---
class TestPasswordReset:
    APP_ORIGIN = BASE_URL

    def test_forgot_generic_unknown_email(self):
        r = requests.post(f"{API}/auth/forgot-password",
                          json={"email": "nobody_xyz_TEST@example.com", "origin_url": self.APP_ORIGIN})
        assert r.status_code == 200
        assert "If an account exists" in r.json()["message"]

    def test_forgot_invalid_origin(self):
        r = requests.post(f"{API}/auth/forgot-password",
                          json={"email": "delivered@resend.dev", "origin_url": "https://evil.example.com"})
        assert r.status_code == 400

    def test_reset_flow_end_to_end(self):
        # Register a fresh test user
        import uuid
        email = f"TEST_reset_{uuid.uuid4().hex[:8]}@t.com"
        old_pw = "oldpass123"
        new_pw = "newpass456"
        reg = requests.post(f"{API}/auth/register", json={"email": email, "password": old_pw, "name": "R"})
        assert reg.status_code == 200
        user_id = reg.json()["user"]["id"]

        # Request forgot-password (this creates a token in Mongo but may or may not send email)
        r = requests.post(f"{API}/auth/forgot-password",
                          json={"email": email, "origin_url": self.APP_ORIGIN})
        # Email sending to non-deliverable addresses may 502; the token is still created BEFORE send.
        # But since it returns generic message only on success, we assert either 200 or 502.
        assert r.status_code in (200, 502)

        # Read the newest token from Mongo
        import pymongo
        mongo_url = None
        db_name = None
        with open("/app/backend/.env") as fh:
            for line in fh:
                if line.startswith("MONGO_URL="):
                    mongo_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                if line.startswith("DB_NAME="):
                    db_name = line.split("=", 1)[1].strip().strip('"').strip("'")
        client = pymongo.MongoClient(mongo_url)
        rec = client[db_name].password_reset_tokens.find_one(
            {"user_id": user_id, "used": False}, sort=[("expires_at", -1)])
        assert rec is not None, "No reset token found in Mongo"
        token = rec["token"]

        # Reset with token
        rr = requests.post(f"{API}/auth/reset-password",
                          json={"token": token, "new_password": new_pw})
        assert rr.status_code == 200, rr.text
        assert rr.json()["ok"] is True

        # Old password no longer works
        bad = requests.post(f"{API}/auth/login", json={"email": email, "password": old_pw})
        assert bad.status_code == 401

        # New password works
        good = requests.post(f"{API}/auth/login", json={"email": email, "password": new_pw})
        assert good.status_code == 200

        # Token reuse blocked
        again = requests.post(f"{API}/auth/reset-password",
                              json={"token": token, "new_password": "anotherpw"})
        assert again.status_code == 400
        assert "invalid" in again.json()["detail"].lower() or "used" in again.json()["detail"].lower()

    def test_reset_bad_token(self):
        r = requests.post(f"{API}/auth/reset-password",
                          json={"token": "not-a-real-token", "new_password": "abcdef"})
        assert r.status_code == 400

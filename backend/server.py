from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import uuid
import asyncio
import logging
import bcrypt
import jwt
import stripe
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import Response as RawResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Optional

import engine
import pf_client
import pdf_reports
import email_service
import secrets
from html import escape

AEST = ZoneInfo("Australia/Sydney")
JWT_ALGORITHM = "HS256"
JWT_SECRET = os.environ["JWT_SECRET"]

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

app = FastAPI(title="PuntRank Aus API")
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("puntrank")


# ---------- auth helpers ----------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email, "type": "access",
               "exp": datetime.now(timezone.utc) + timedelta(days=7)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _set_cookies(response: Response, token: str):
    response.set_cookie("access_token", token, httponly=True, secure=True,
                        samesite="none", max_age=604800, path="/")


def _public_user(u: dict) -> dict:
    return {"id": u["id"], "email": u["email"], "name": u.get("name", ""),
            "is_pro": bool(u.get("is_pro")), "role": u.get("role", "user"),
            "pro_plan": u.get("pro_plan")}


async def _user_from_request(request: Request) -> Optional[dict]:
    token = None
    ah = request.headers.get("Authorization", "")
    if ah.startswith("Bearer "):
        token = ah[7:]
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
    except jwt.InvalidTokenError:
        return None


async def get_current_user(request: Request) -> dict:
    user = await _user_from_request(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    return user


async def get_optional_user(request: Request) -> Optional[dict]:
    return await _user_from_request(request)


async def get_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    return user


def is_pro(user: Optional[dict]) -> bool:
    return bool(user and (user.get("is_pro") or user.get("role") == "admin"))


# ---------- models ----------
class RegisterInput(BaseModel):
    email: str
    password: str = Field(min_length=6)
    name: str = ""
    origin_url: str = ""


class LoginInput(BaseModel):
    email: str
    password: str


class CheckoutRequest(BaseModel):
    lookup_key: str
    origin_url: str


class ForgotPasswordInput(BaseModel):
    email: str
    origin_url: str


class ResetPasswordInput(BaseModel):
    token: str
    new_password: str = Field(min_length=6)


ALLOWED_ORIGIN_SUFFIXES = (".preview.emergentagent.com", ".emergent.host", "puntrank.com.au", "localhost:3000")


def _validate_origin(origin_url: str) -> str:
    from urllib.parse import urlparse
    parsed = urlparse(origin_url)
    host = parsed.netloc
    if parsed.scheme not in ("https", "http") or not host or parsed.query or parsed.fragment or parsed.path.strip("/"):
        raise HTTPException(400, "Invalid origin")
    if not any(host == s.lstrip(".") or host.endswith(s) for s in ALLOWED_ORIGIN_SUFFIXES):
        raise HTTPException(400, "Invalid origin")
    return f"{parsed.scheme}://{host}"


# ---------- auth routes ----------
async def _send_welcome_email(email: str, name: str, origin: str):
    try:
        date = today_aest()
        meetings = await db.meetings.find({"date": date}, {"_id": 0, "id": 1, "track": 1}).to_list(20)
        mmap = {m["id"]: m["track"] for m in meetings}
        pick = await db.runners.find({"meeting_id": {"$in": list(mmap)}, "grade": "A"},
                                     {"_id": 0}).sort("confidence", -1).to_list(1)
        pick_html = ""
        if pick:
            p = pick[0]
            race = await db.races.find_one({"id": p["race_id"]}, {"_id": 0, "number": 1})
            pick_html = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;margin:0 0 22px"><tr><td style="padding:14px 18px;font-family:Arial,sans-serif">'
                         f'<p style="margin:0;font-size:11px;font-weight:bold;color:#059669;letter-spacing:1px">TODAY&#39;S TOP PICK</p>'
                         f'<p style="margin:4px 0 0;font-size:15px;font-weight:bold;color:#111827">{p["number"]}. {escape(p["name"])}</p>'
                         f'<p style="margin:2px 0 0;font-size:12px;color:#6b7280">{escape(mmap.get(p["meeting_id"], ""))} R{race["number"] if race else "?"} · Confidence {p["confidence"]}/100</p>'
                         f'</td></tr></table>')
        first_name = escape((name or "there").split(" ")[0])
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background-color:#f4f5f6">
<div style="display:none;max-height:0;overflow:hidden">Your form-analysis toolkit is ready — here's how to read the grades.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f6;padding:28px 12px">
<tr><td align="center">
<table role="presentation" width="520" cellpadding="0" cellspacing="0" style="max-width:520px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e5e7eb">
  <tr><td style="background:#0A0D0E;padding:22px 28px" align="center">
    <span style="font-family:Arial Black,Arial,sans-serif;font-size:22px;font-weight:900;letter-spacing:1px;color:#ffffff">PUNT<span style="color:#10B981">RANK</span> <span style="color:#F59E0B;font-size:12px;vertical-align:top">AUS</span></span>
  </td></tr>
  <tr><td style="padding:30px 28px;font-family:Arial,Helvetica,sans-serif;color:#1f2937">
    <h1 style="margin:0 0 14px;font-size:20px;color:#111827">Welcome aboard, {first_name} 🏇</h1>
    <p style="margin:0 0 18px;font-size:14px;line-height:1.6">Your PuntRank Aus account is ready. Every race day we rank today&#39;s runners with win and place probabilities, confidence scores and plain-English reasoning — <b>A grade</b> for the strongest bets, <b>B</b> for solid chances, <b>C</b> for place hopes and exotics.</p>
    {pick_html}
    <table role="presentation" cellpadding="0" cellspacing="0" align="center"><tr><td style="border-radius:28px;background:#059669" align="center">
      <a href="{origin}/guide" style="display:inline-block;padding:13px 34px;font-family:Arial,sans-serif;font-size:14px;font-weight:bold;color:#ffffff;text-decoration:none;border-radius:28px">See how it works</a>
    </td></tr></table>
    <p style="margin:16px 0 0;font-size:12px;line-height:1.6;color:#6b7280;word-break:break-all">Or paste this link into your browser:<br><a href="{origin}/guide" style="color:#059669">{origin}/guide</a></p>
  </td></tr>
  <tr><td style="padding:16px 28px;background:#f9fafb;border-top:1px solid #e5e7eb;font-family:Arial,sans-serif" align="center">
    <p style="margin:0;font-size:11px;color:#6b7280;line-height:1.6">Sent by {escape(email_service.EMAIL_FROM_NAME)} — a probability-ranking tool, not a betting service.<br>18+ only · Gamble responsibly · Gambling Help 1800 858 858</p>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""
        await email_service.send_email(to=email, subject="Welcome to PuntRank Aus — your form toolkit is ready", html=html)
    except Exception:
        logger.warning(f"Welcome email could not be delivered to {email}")


@api.post("/auth/register")
async def register(body: RegisterInput, response: Response):
    email = body.email.strip().lower()
    if "@" not in email or "." not in email:
        raise HTTPException(400, "Enter a valid email address")
    if await db.users.find_one({"email": email}):
        raise HTTPException(400, "An account with this email already exists")
    user = {"id": str(uuid.uuid4()), "email": email, "name": body.name.strip(),
            "password_hash": hash_password(body.password), "role": "user",
            "is_pro": False, "pro_plan": None,
            "created_at": datetime.now(timezone.utc).isoformat()}
    await db.users.insert_one({**user})
    if body.origin_url:
        try:
            origin = _validate_origin(body.origin_url)
            asyncio.create_task(_send_welcome_email(email, user["name"], origin))
        except Exception:
            pass
    token = create_access_token(user["id"], email)
    _set_cookies(response, token)
    return {"user": _public_user(user), "access_token": token}


@api.post("/auth/login")
async def login(body: LoginInput, request: Request, response: Response):
    email = body.email.strip().lower()
    ident = f"{request.client.host}:{email}"
    attempt = await db.login_attempts.find_one({"identifier": ident})
    now = datetime.now(timezone.utc)
    if attempt and attempt.get("count", 0) >= 5:
        locked_at = datetime.fromisoformat(attempt["last_at"])
        if now - locked_at < timedelta(minutes=15):
            raise HTTPException(429, "Too many failed attempts. Try again in 15 minutes.")
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user or not verify_password(body.password, user["password_hash"]):
        await db.login_attempts.update_one(
            {"identifier": ident},
            {"$inc": {"count": 1}, "$set": {"last_at": now.isoformat()}}, upsert=True)
        raise HTTPException(401, "Incorrect email or password")
    await db.login_attempts.delete_one({"identifier": ident})
    token = create_access_token(user["id"], email)
    _set_cookies(response, token)
    return {"user": _public_user(user), "access_token": token}


@api.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}


@api.post("/auth/forgot-password")
async def forgot_password(body: ForgotPasswordInput):
    origin = _validate_origin(body.origin_url)
    email = body.email.strip().lower()
    user = await db.users.find_one({"email": email}, {"_id": 0})
    generic = {"ok": True, "message": "If an account exists for that email, a reset link has been sent."}
    if not user:
        return generic
    token = secrets.token_urlsafe(32)
    await db.password_reset_tokens.insert_one({
        "token": token, "user_id": user["id"], "used": False,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1)})
    link = f"{origin}/reset-password?token={token}"
    first_name = escape((user.get("name") or "there").split(" ")[0])
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background-color:#f4f5f6">
<div style="display:none;max-height:0;overflow:hidden">Tap the button to set a new PuntRank Aus password — link expires in 1 hour.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f6;padding:28px 12px">
<tr><td align="center">
<table role="presentation" width="520" cellpadding="0" cellspacing="0" style="max-width:520px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e5e7eb">
  <tr><td style="background:#0A0D0E;padding:22px 28px" align="center">
    <span style="font-family:Arial Black,Arial,sans-serif;font-size:22px;font-weight:900;letter-spacing:1px;color:#ffffff">PUNT<span style="color:#10B981">RANK</span> <span style="color:#F59E0B;font-size:12px;vertical-align:top">AUS</span></span>
  </td></tr>
  <tr><td style="padding:30px 28px;font-family:Arial,Helvetica,sans-serif;color:#1f2937">
    <h1 style="margin:0 0 14px;font-size:20px;color:#111827">Reset your password</h1>
    <p style="margin:0 0 10px;font-size:14px;line-height:1.6">G'day {first_name},</p>
    <p style="margin:0 0 22px;font-size:14px;line-height:1.6">We received a request to reset the password for your PuntRank Aus account. Tap the button below to choose a new one.</p>
    <table role="presentation" cellpadding="0" cellspacing="0" align="center"><tr><td style="border-radius:28px;background:#059669" align="center">
      <a href="{link}" style="display:inline-block;padding:13px 34px;font-family:Arial,sans-serif;font-size:14px;font-weight:bold;color:#ffffff;text-decoration:none;border-radius:28px">Set a new password</a>
    </td></tr></table>
    <p style="margin:16px 0 0;font-size:12px;line-height:1.6;color:#6b7280;word-break:break-all">Or paste this link into your browser:<br><a href="{link}" style="color:#059669">{link}</a></p>
    <p style="margin:22px 0 0;font-size:12px;line-height:1.6;color:#6b7280">This link expires in 1 hour and can only be used once. If you didn't request this, you can safely ignore this email — your password won't change.</p>
  </td></tr>
  <tr><td style="padding:16px 28px;background:#f9fafb;border-top:1px solid #e5e7eb;font-family:Arial,sans-serif" align="center">
    <p style="margin:0;font-size:11px;color:#6b7280;line-height:1.6">Sent by {escape(email_service.EMAIL_FROM_NAME)} — a probability-ranking tool, not a betting service.<br>We never ask for your password or card details by email.<br>18+ only · Gamble responsibly · Gambling Help 1800 858 858</p>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""
    async def _send():
        try:
            await email_service.send_email(to=email, subject="Reset your PuntRank Aus password", html=html)
        except Exception:
            logger.warning(f"Reset email could not be delivered to {email}")
    asyncio.create_task(_send())
    return generic


@api.post("/auth/reset-password")
async def reset_password(body: ResetPasswordInput):
    rec = await db.password_reset_tokens.find_one({"token": body.token}, {"_id": 0})
    if not rec or rec.get("used"):
        raise HTTPException(400, "This reset link is invalid or has already been used")
    expires = rec["expires_at"]
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        raise HTTPException(400, "This reset link has expired — request a new one")
    await db.users.update_one({"id": rec["user_id"]},
                              {"$set": {"password_hash": hash_password(body.new_password)}})
    await db.password_reset_tokens.update_one({"token": body.token}, {"$set": {"used": True}})
    return {"ok": True, "message": "Password updated — you can now sign in"}


@api.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return _public_user(user)


# ---------- racing data ----------
def today_aest() -> str:
    return datetime.now(AEST).strftime("%Y-%m-%d")


async def ensure_seed(force: bool = False):
    date = today_aest()
    exists = await db.meetings.find_one({"date": date})
    if exists and not force:
        return
    if force:
        # manual admin reseed only: replace today's data and purge >30-day-old data
        todays = await db.meetings.find({"date": date}, {"_id": 0, "id": 1}).to_list(50)
        cutoff = (datetime.now(AEST) - timedelta(days=30)).strftime("%Y-%m-%d")
        old = await db.meetings.find({"date": {"$lt": cutoff}}, {"_id": 0, "id": 1}).to_list(1000)
        stale = [m["id"] for m in todays + old]
        if stale:
            await db.races.delete_many({"meeting_id": {"$in": stale}})
            await db.runners.delete_many({"meeting_id": {"$in": stale}})
            await db.meetings.delete_many({"id": {"$in": stale}})
    meetings, races, runners = [], [], []
    if os.environ.get("PUNTING_FORM_API_KEY"):
        try:
            if await pf_client.load_today(db, date):
                return
        except Exception as e:
            logger.warning(f"Punting Form load failed, falling back to mock data: {e!r}")
    meetings, races, runners = engine.seed_day(date, datetime.now(AEST))
    await db.meetings.insert_many([{**m} for m in meetings])
    await db.races.insert_many([{**r} for r in races])
    await db.runners.insert_many([{**r} for r in runners])
    logger.info(f"Seeded {len(meetings)} mock meetings / {len(races)} races for {date}")


async def _pf_sync_bg(date: str):
    try:
        await pf_client.sync_results(db, date)
    except Exception as e:
        logger.warning(f"PF results sync failed: {e!r}")


async def _grade_started_races():
    """Grade finished races: official PF results for live data, simulation for mock data."""
    now = datetime.now(AEST)
    date = today_aest()
    if await db.meetings.find_one({"date": date, "source": "punting_form"}):
        meta = await db.meta.find_one({"key": "pf_results_sync"})
        if not meta or (now - datetime.fromisoformat(meta["at"])).total_seconds() > 180:
            await db.meta.update_one({"key": "pf_results_sync"},
                                     {"$set": {"at": now.isoformat()}}, upsert=True)
            asyncio.create_task(_pf_sync_bg(date))
        return
    pending = await db.races.find({"status": "upcoming"}, {"_id": 0}).to_list(500)
    import random as _rnd
    for race in pending:
        if datetime.fromisoformat(race["start_aest"]) > now:
            continue
        rs = await db.runners.find({"race_id": race["id"], "scratched": False}, {"_id": 0}).to_list(50)
        if not rs:
            continue
        pool = list(rs)
        order = []
        for _ in range(min(4, len(pool))):
            pick = _rnd.choices(pool, weights=[r["win_prob"] for r in pool])[0]
            order.append(pick["number"])
            pool.remove(pick)
        top = min(rs, key=lambda x: x["rank"])
        win_r = next(x for x in rs if x["number"] == order[0])
        await db.races.update_one({"id": race["id"]}, {"$set": {
            "status": "resulted",
            "result": {"positions": order, "win_dividend": round(win_r["odds_current"], 2),
                       "top_pick_won": top["number"] == order[0],
                       "top_pick_placed": top["number"] in order[:3]}}})


@api.get("/meetings")
async def get_meetings():
    await ensure_seed()
    await _grade_started_races()
    date = today_aest()
    meetings = await db.meetings.find({"date": date}, {"_id": 0}).to_list(20)
    all_races = await db.races.find({"meeting_id": {"$in": [m["id"] for m in meetings]}},
                                    {"_id": 0}).sort("number", 1).to_list(300)
    races_by_meeting = {}
    for r in all_races:
        races_by_meeting.setdefault(r["meeting_id"], []).append(r)
    out = []
    for m in meetings:
        races = races_by_meeting.get(m["id"], [])
        nxt = next((r for r in races if r["status"] == "upcoming"), None)
        out.append({**m, "resulted": sum(1 for r in races if r["status"] == "resulted"),
                    "next_race": {"number": nxt["number"], "start_aest": nxt["start_aest"]} if nxt else None})
    return {"date_aest": date, "now_aest": datetime.now(AEST).isoformat(), "meetings": out}


@api.get("/meetings/{meeting_id}/races")
async def get_races(meeting_id: str):
    await _grade_started_races()
    meeting = await db.meetings.find_one({"id": meeting_id}, {"_id": 0})
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    races = await db.races.find({"meeting_id": meeting_id}, {"_id": 0}).sort("number", 1).to_list(20)
    return {"meeting": meeting, "races": races}


@api.get("/races/{race_id}")
async def get_race(race_id: str, user: Optional[dict] = Depends(get_optional_user)):
    race = await db.races.find_one({"id": race_id}, {"_id": 0})
    if not race:
        raise HTTPException(404, "Race not found")
    runners = await db.runners.find({"race_id": race_id}, {"_id": 0}).sort("rank", 1).to_list(50)
    meeting = await db.meetings.find_one({"id": race["meeting_id"]}, {"_id": 0})
    pro = is_pro(user)
    if not pro:
        for r in runners:
            if r["rank"] > 3:
                r["reasoning"] = None
                r["confidence"] = None
    return {"race": race, "meeting": meeting, "runners": runners, "pro": pro}


@api.get("/races/{race_id}/exotics")
async def get_exotics(race_id: str, user: Optional[dict] = Depends(get_optional_user)):
    runners = await db.runners.find({"race_id": race_id}, {"_id": 0}).to_list(50)
    if not runners:
        raise HTTPException(404, "Race not found")
    exotics = engine.build_exotics(runners)
    if not is_pro(user):
        return {"exotics": exotics[:1], "locked": len(exotics) - 1, "pro": False}
    return {"exotics": exotics, "locked": 0, "pro": True}


@api.get("/selections/aces")
async def aces_selections(user: Optional[dict] = Depends(get_optional_user)):
    await ensure_seed()
    date = today_aest()
    meetings = await db.meetings.find({"date": date}, {"_id": 0}).to_list(20)
    mmap = {m["id"]: m for m in meetings}
    races = await db.races.find({"meeting_id": {"$in": list(mmap)}}, {"_id": 0}).to_list(200)
    rmap = {r["id"]: r for r in races}
    winners = await db.runners.find({"meeting_id": {"$in": list(mmap)}, "aces_win": True}, {"_id": 0}).to_list(100)
    places = await db.runners.find({"meeting_id": {"$in": list(mmap)}, "aces_place": True}, {"_id": 0}).to_list(100)

    def decorate(rs):
        out = []
        for r in sorted(rs, key=lambda x: -x["win_prob"]):
            race = rmap[r["race_id"]]
            out.append({**r, "track": mmap[r["meeting_id"]]["track"], "race_number": race["number"],
                        "start_aest": race["start_aest"], "race_status": race["status"],
                        "result": race.get("result")})
        return out

    feature = next((m for m in meetings if m.get("feature")), None)
    quaddie = []
    if feature:
        legs = sorted([r for r in races if r.get("is_quaddie_leg")], key=lambda x: x["number"])
        leg_runners = await db.runners.find({"race_id": {"$in": [x["id"] for x in legs]},
                                             "rank": {"$lte": 2}}, {"_id": 0}).sort("rank", 1).to_list(50)
        by_leg = {}
        for r in leg_runners:
            by_leg.setdefault(r["race_id"], []).append(r)
        for i, leg in enumerate(legs, 1):
            quaddie.append({"leg": i, "race_number": leg["number"], "distance": leg["distance"],
                            "start_aest": leg["start_aest"], "selections": by_leg.get(leg["id"], [])})
    pro = is_pro(user)
    win_list = decorate(winners)
    place_list = decorate(places)
    if not pro:
        win_list, place_list, quaddie = win_list[:2], place_list[:1], quaddie[:1]
    return {"winners": win_list, "places": place_list, "quaddie": quaddie,
            "quaddie_track": feature["track"] if feature else None, "pro": pro}


@api.get("/best-bets")
async def best_bets(user: Optional[dict] = Depends(get_optional_user)):
    await ensure_seed()
    await _grade_started_races()
    date = today_aest()
    meetings = await db.meetings.find({"date": date}, {"_id": 0}).to_list(20)
    mmap = {m["id"]: m for m in meetings}
    races = await db.races.find({"meeting_id": {"$in": list(mmap)}}, {"_id": 0}).to_list(200)
    rmap = {r["id"]: r for r in races}
    a_grade = await db.runners.find({"meeting_id": {"$in": list(mmap)}, "grade": "A"}, {"_id": 0}).to_list(100)
    a_grade.sort(key=lambda x: (-(x["confidence"] or 0), -x["win_prob"]))
    out = []
    for r in a_grade:
        race = rmap[r["race_id"]]
        res = race.get("result")
        graded = None
        if res:
            graded = "WON" if r["number"] == res["positions"][0] else (
                "PLACED" if r["number"] in res["positions"][:3] else "UNPLACED")
        out.append({**r, "track": mmap[r["meeting_id"]]["track"], "race_number": race["number"],
                    "start_aest": race["start_aest"], "race_status": race["status"], "graded": graded})
    upcoming = [b for b in out if b["race_status"] == "upcoming"][:3]
    multis = []
    if len(upcoming) >= 2:
        combined = upcoming[0]["odds_current"] * upcoming[1]["odds_current"]
        multis.append({"name": "A-Grade Double", "legs": upcoming[:2], "combined_odds": round(combined, 2)})
    if len(upcoming) >= 3:
        combined = upcoming[0]["odds_current"] * upcoming[1]["odds_current"] * upcoming[2]["odds_current"]
        multis.append({"name": "A-Grade Treble", "legs": upcoming[:3], "combined_odds": round(combined, 2)})
    pro = is_pro(user)
    if not pro:
        return {"bets": out[:1], "locked": max(0, len(out) - 1), "multis": [], "pro": False}
    return {"bets": out, "locked": 0, "multis": multis, "pro": True}


@api.get("/movers")
async def market_movers():
    await ensure_seed()
    date = today_aest()
    meetings = await db.meetings.find({"date": date}, {"_id": 0}).to_list(20)
    mmap = {m["id"]: m for m in meetings}
    races = await db.races.find({"meeting_id": {"$in": list(mmap)}}, {"_id": 0}).to_list(200)
    rmap = {r["id"]: r for r in races}
    movers = await db.runners.find({"meeting_id": {"$in": list(mmap)},
                                    "$expr": {"$gt": ["$odds_open", "$odds_current"]}},
                                   {"_id": 0}).to_list(300)
    out = []
    for r in movers:
        pct = (r["odds_open"] - r["odds_current"]) / r["odds_open"] * 100
        if pct < 8:
            continue
        race = rmap[r["race_id"]]
        out.append({**r, "move_pct": round(pct, 1), "track": mmap[r["meeting_id"]]["track"],
                    "race_number": race["number"], "start_aest": race["start_aest"],
                    "race_status": race["status"]})
    out.sort(key=lambda x: -x["move_pct"])
    return {"movers": out[:25]}


@api.get("/results")
async def results():
    await ensure_seed()
    await _grade_started_races()
    date = today_aest()
    meetings = await db.meetings.find({"date": date}, {"_id": 0}).to_list(20)
    mmap = {m["id"]: m for m in meetings}
    races = await db.races.find({"meeting_id": {"$in": list(mmap)}, "status": "resulted"},
                                {"_id": 0}).to_list(200)
    races.sort(key=lambda x: x["start_aest"], reverse=True)
    out = []
    for race in races:
        rs = await db.runners.find({"race_id": race["id"]}, {"_id": 0}).to_list(50)
        num_map = {r["number"]: r for r in rs}
        top = min(rs, key=lambda x: x["rank"])
        placings = [{"pos": i + 1, "number": n, "name": num_map[n]["name"],
                     "odds": num_map[n]["odds_current"]}
                    for i, n in enumerate(race["result"]["positions"]) if n in num_map]
        out.append({"race_id": race["id"], "track": mmap[race["meeting_id"]]["track"],
                    "race_number": race["number"], "name": race["name"], "distance": race["distance"],
                    "start_aest": race["start_aest"], "placings": placings,
                    "win_dividend": race["result"]["win_dividend"],
                    "top_pick": {"number": top["number"], "name": top["name"]},
                    "top_pick_won": race["result"]["top_pick_won"],
                    "top_pick_placed": race["result"]["top_pick_placed"]})
    n = len(out)
    wins = sum(1 for r in out if r["top_pick_won"])
    places = sum(1 for r in out if r["top_pick_placed"])
    return {"results": out, "stats": {"resulted": n, "wins": wins, "places": places,
                                      "win_strike": round(wins / n * 100, 1) if n else 0,
                                      "place_strike": round(places / n * 100, 1) if n else 0}}


# ---------- PDF reports ----------
REPORTS = [
    {"key": "form_guide", "title": "Saturday Form Guide", "desc": "Full-day form for every meeting: rankings, probabilities and grades.", "pro": False},
    {"key": "top10", "title": "Ace's Top 10 Picks", "desc": "Ace's 10 highest-rated runners across all tracks today — the daily shortlist.", "pro": False},
    {"key": "results_wrap", "title": "Sunday Results Wrap", "desc": "Every resulted race graded against Ace's top picks.", "pro": True},
    {"key": "scorecard", "title": "A-Grade Scorecard", "desc": "Units won/lost following the top pick in every resulted race.", "pro": True},
    {"key": "staking", "title": "Staking Calculator", "desc": "Confidence-based unit staking plan with bankroll rules.", "pro": True},
    {"key": "quaddie", "title": "Ace's Quaddie Ticket", "desc": "Printable quaddie for the feature meeting — 2 selections per leg with flexi costs.", "pro": True},
]


@api.get("/reports")
async def list_reports(user: Optional[dict] = Depends(get_optional_user)):
    return {"reports": REPORTS, "pro": is_pro(user)}


@api.get("/reports/{key}/download")
async def download_report(key: str, user: Optional[dict] = Depends(get_optional_user)):
    meta = next((r for r in REPORTS if r["key"] == key), None)
    if not meta:
        raise HTTPException(404, "Unknown report")
    if meta["pro"] and not is_pro(user):
        raise HTTPException(402, "Pro subscription required for this report")
    await ensure_seed()
    await _grade_started_races()
    date = today_aest()
    meetings = await db.meetings.find({"date": date}, {"_id": 0}).to_list(20)
    mmap = {m["id"]: m for m in meetings}
    races = await db.races.find({"meeting_id": {"$in": list(mmap)}}, {"_id": 0}).to_list(200)
    races_map = {r["id"]: r for r in races}
    all_runners = await db.runners.find({"meeting_id": {"$in": list(mmap)}}, {"_id": 0}).to_list(2000)
    by_race = {}
    for r in all_runners:
        by_race.setdefault(r["race_id"], []).append(r)
    resulted = sorted([r for r in races if r["status"] == "resulted"], key=lambda x: x["start_aest"])

    if key == "form_guide":
        data = pdf_reports.form_guide_pdf(date, meetings, sorted(races, key=lambda x: x["number"]), by_race)
    elif key == "top10":
        picks = sorted(all_runners, key=lambda x: -x["win_prob"])
        data = pdf_reports.top10_pdf(date, picks, mmap, races_map)
    elif key == "results_wrap":
        data = pdf_reports.results_wrap_pdf(date, meetings, resulted, by_race)
    elif key == "scorecard":
        data = pdf_reports.scorecard_pdf(date, resulted, mmap)
    elif key == "staking":
        data = pdf_reports.staking_pdf(date)
    else:
        feature = next((m for m in meetings if m.get("feature")), meetings[0])
        legs = sorted([r for r in races if r.get("is_quaddie_leg")], key=lambda x: x["number"])
        leg_data = []
        for i, leg in enumerate(legs, 1):
            sel = sorted(by_race.get(leg["id"], []), key=lambda x: x["rank"])[:2]
            leg_data.append({"leg": i, "race_number": leg["number"], "distance": leg["distance"], "selections": sel})
        data = pdf_reports.quaddie_pdf(date, feature["track"], leg_data)
    return RawResponse(content=data, media_type="application/pdf",
                       headers={"Content-Disposition": f'attachment; filename="puntrank_{key}_{date}.pdf"'})


# ---------- payments (Stripe) ----------
async def _grant_pro(session_id: str):
    tx = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not tx or not tx.get("user_id"):
        return
    await db.users.update_one({"id": tx["user_id"]},
                              {"$set": {"is_pro": True, "pro_plan": tx["lookup_key"],
                                        "pro_since": datetime.now(timezone.utc).isoformat()}})


@api.get("/payments/plans")
async def payment_plans():
    return {"plans": [
        {"lookup_key": "pro_monthly", "label": "Monthly", "price": "A$9.99", "period": "/month", "note": "Cancel anytime"},
        {"lookup_key": "pro_annual", "label": "Annual", "price": "A$49.99", "period": "/year", "note": "Save 58%"},
        {"lookup_key": "pro_lifetime", "label": "Lifetime", "price": "A$99.00", "period": "one-off", "note": "Pay once, Pro forever"},
    ]}


@api.post("/payments/checkout")
async def create_checkout(req: CheckoutRequest, user: dict = Depends(get_current_user)):
    prices = stripe.Price.list(lookup_keys=[req.lookup_key], active=True, limit=1).data
    if not prices:
        raise HTTPException(500, f"Price not found: {req.lookup_key}")
    price = prices[0]
    kwargs = dict(
        line_items=[{"price": price.id, "quantity": 1}],
        mode="subscription" if price.recurring else "payment",
        success_url=f"{req.origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{req.origin_url}/pricing",
        metadata={"user_id": user["id"], "lookup_key": req.lookup_key},
    )
    try:
        session = stripe.checkout.Session.create(**kwargs, managed_payments={"enabled": True})
    except stripe.error.InvalidRequestError as e:
        msg = (e.user_message or "").lower()
        if "managed payments" in msg or "ineligible" in msg:
            session = stripe.checkout.Session.create(
                **kwargs, automatic_tax={"enabled": True}, billing_address_collection="required")
        else:
            raise
    await db.payment_transactions.insert_one({
        "session_id": session.id, "user_id": user["id"], "lookup_key": req.lookup_key,
        "amount": float(price.unit_amount or 0), "currency": price.currency,
        "status": "initiated", "payment_status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()})
    return {"checkout_url": session.url, "session_id": session.id}


@api.get("/payments/status/{session_id}")
async def payment_status(session_id: str):
    record = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not record:
        raise HTTPException(404, "Transaction not found")
    if record.get("payment_status") != "paid":
        try:
            s = stripe.checkout.Session.retrieve(session_id)
            if s.payment_status == "paid" or s.status == "complete":
                await db.payment_transactions.update_one(
                    {"session_id": session_id, "payment_status": {"$ne": "paid"}},
                    {"$set": {"status": "completed", "payment_status": "paid",
                              "stripe_subscription_id": s.subscription,
                              "stripe_payment_intent_id": s.payment_intent,
                              "updated_at": datetime.now(timezone.utc).isoformat()}})
                await _grant_pro(session_id)
                record = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
        except stripe.error.StripeError:
            pass
    return {"session_id": record["session_id"], "status": record["status"],
            "payment_status": record["payment_status"]}


@api.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")
    obj, t = event["data"]["object"], event["type"]
    now = datetime.now(timezone.utc).isoformat()
    if t == "checkout.session.completed":
        await db.payment_transactions.update_one(
            {"session_id": obj["id"], "payment_status": {"$ne": "paid"}},
            {"$set": {"status": "completed", "payment_status": obj.get("payment_status", "paid"),
                      "stripe_subscription_id": obj.get("subscription"),
                      "stripe_payment_intent_id": obj.get("payment_intent"), "updated_at": now}})
        await _grant_pro(obj["id"])
    elif t == "checkout.session.async_payment_succeeded":
        await db.payment_transactions.update_one({"session_id": obj["id"]},
            {"$set": {"payment_status": "paid", "updated_at": now}})
        await _grant_pro(obj["id"])
    elif t == "checkout.session.async_payment_failed":
        await db.payment_transactions.update_one({"session_id": obj["id"]},
            {"$set": {"status": "failed", "payment_status": "failed", "updated_at": now}})
    elif t == "checkout.session.expired":
        await db.payment_transactions.update_one({"session_id": obj["id"]},
            {"$set": {"status": "expired", "payment_status": "expired", "updated_at": now}})
    elif t == "charge.refunded":
        await db.payment_transactions.update_one({"stripe_payment_intent_id": obj.get("payment_intent")},
            {"$set": {"status": "refunded", "payment_status": "refunded", "updated_at": now}})
    return {"status": "ok"}


# ---------- admin ----------
@api.post("/admin/reseed")
async def admin_reseed(admin: dict = Depends(get_admin)):
    await ensure_seed(force=True)
    return {"ok": True, "date": today_aest()}


@api.get("/admin/users")
async def admin_users(admin: dict = Depends(get_admin)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(500)
    return {"users": users}


@api.get("/admin/payments")
async def admin_payments(admin: dict = Depends(get_admin)):
    txs = await db.payment_transactions.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    uids = list({t.get("user_id") for t in txs if t.get("user_id")})
    emails = {u["id"]: u["email"] async for u in db.users.find({"id": {"$in": uids}}, {"_id": 0, "id": 1, "email": 1})}
    for t in txs:
        t["amount"] = round(t.get("amount", 0) / 100, 2)
        t["email"] = emails.get(t.get("user_id"))
    paid = [t for t in txs if t.get("payment_status") == "paid"]
    revenue = round(sum(t.get("amount", 0) for t in paid), 2)
    return {"transactions": txs, "paid_count": len(paid), "revenue": revenue,
            "mode": os.environ.get("STRIPE_MODE", "test")}


@api.post("/admin/users/{user_id}/toggle-pro")
async def toggle_pro(user_id: str, admin: dict = Depends(get_admin)):
    u = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not u:
        raise HTTPException(404, "User not found")
    new_val = not u.get("is_pro")
    await db.users.update_one({"id": user_id},
                              {"$set": {"is_pro": new_val, "pro_plan": "admin_grant" if new_val else None}})
    return {"ok": True, "is_pro": new_val}


@api.get("/")
async def root():
    return {"app": "PuntRank Aus API", "date_aest": today_aest()}


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id")
    await db.runners.create_index("race_id")
    await db.races.create_index("meeting_id")
    await db.login_attempts.create_index("identifier")
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.password_reset_tokens.create_index("token")
    admin_email = os.environ["ADMIN_EMAIL"]
    admin_password = os.environ["ADMIN_PASSWORD"]
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({"id": str(uuid.uuid4()), "email": admin_email,
                                   "password_hash": hash_password(admin_password), "name": "Ace Admin",
                                   "role": "admin", "is_pro": True, "pro_plan": "admin",
                                   "created_at": datetime.now(timezone.utc).isoformat()})
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email},
                                  {"$set": {"password_hash": hash_password(admin_password)}})
    await ensure_seed()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

import os
import uuid
import logging
import httpx
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

AEST = ZoneInfo("Australia/Sydney")
BASE = "https://api.puntingform.com.au/v2"
logger = logging.getLogger("puntrank.pf")


def _key():
    return os.environ.get("PUNTING_FORM_API_KEY", "")


async def _get(path, retries=2, **params):
    params["apiKey"] = _key()
    last = None
    for _ in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=30) as cl:
                r = await cl.get(f"{BASE}/{path}", params=params)
                r.raise_for_status()
                data = r.json()
                if data.get("statusCode") != 200:
                    raise RuntimeError(f"PF error: {data.get('error')}")
                return data["payLoad"]
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last = e
    raise RuntimeError(f"PF request failed after retries: {path} ({last!r})")


def _parse_utc(s):
    dt = datetime.strptime(s, "%m/%d/%Y %I:%M:%S %p").replace(tzinfo=timezone.utc)
    return dt.astimezone(AEST)


def _rec_rate(rec):
    if not rec or not rec.get("starts"):
        return None
    return rec["firsts"] / rec["starts"]


def _last10_score(last10):
    s = (last10 or "").strip().replace(" ", "")
    pts, weight, total_w = 0.0, 1.0, 0.0
    for ch in reversed(s[-6:]):
        if ch == "x":
            continue
        v = {"1": 10, "2": 7, "3": 5, "4": 3, "5": 2}.get(ch, 0.5 if ch != "0" else 0.2)
        pts += v * weight
        total_w += weight
        weight *= 0.75
    return pts / total_w if total_w else 3.0


def _score_runner(r, field_avg_weight):
    win_pct = r.get("winPct") or 0
    place_pct = r.get("placePct") or 0
    score = 20.0
    score += min(35.0, win_pct * 0.9)
    score += min(12.0, place_pct * 0.22)
    score += _last10_score(r.get("last10")) * 2.2
    dist = _rec_rate(r.get("distanceRecord"))
    if dist is not None:
        score += dist * 14
    trk = _rec_rate(r.get("trackRecord"))
    if trk is not None:
        score += trk * 8
    td = _rec_rate(r.get("trackDistRecord"))
    if td is not None:
        score += td * 8
    barrier = r.get("barrier") or 8
    if barrier <= 4:
        score += 3
    elif barrier >= 12:
        score -= 3
    wt = r.get("weightTotal") or r.get("weight") or field_avg_weight
    score -= (wt - field_avg_weight) * 1.2
    if not (r.get("jockey") or {}).get("name", "").strip():
        score -= 4
    starts = r.get("careerStarts") or 0
    if starts == 0:
        score -= 2
    return max(1.0, score)


def _reasoning(r, rank, prob):
    bits = []
    starts, wins = r.get("careerStarts") or 0, r.get("careerWins") or 0
    if starts:
        bits.append(f"career record {wins} wins from {starts} starts ({r.get('winPct', 0):.0f}% win, {r.get('placePct', 0):.0f}% place)")
    else:
        bits.append("first starter — market watch advised")
    dist = r.get("distanceRecord") or {}
    if dist.get("starts") and dist.get("firsts"):
        bits.append(f"proven at the trip with {dist['firsts']} win(s) from {dist['starts']} tries at the distance")
    td = r.get("trackDistRecord") or {}
    if td.get("firsts"):
        bits.append("has won at this track and distance before")
    last10 = (r.get("last10") or "").strip()
    if last10:
        recent = last10[-3:].replace("x", "-")
        bits.append(f"recent form reads {recent}")
    barrier = r.get("barrier")
    if barrier and barrier <= 4:
        bits.append(f"drawn to get the run of the race from barrier {barrier}")
    elif barrier and barrier >= 12:
        bits.append(f"faces a task from the wide gate ({barrier})")
    jockey = (r.get("jockey") or {}).get("fullName", "").strip()
    if jockey:
        bits.append(f"{jockey} takes the ride")
    lead = ["Top pick — ", "Strong claims — ", "Each-way value — ", "Knockout hope — "][min(rank, 3)]
    return lead + "; ".join(bits[:4]) + f". Rated a {prob*100:.0f}% winning chance by the PuntRank model."


async def load_today(db, date_aest: str) -> bool:
    """Fetch today's AUS meetings from Punting Form into meetings/races/runners collections."""
    pf_date = datetime.strptime(date_aest, "%Y-%m-%d").strftime("%d-%b-%Y")
    meetings_raw = await _get("form/meetingslist", meetingDate=pf_date)
    candidates = [m for m in meetings_raw
                  if m.get("tabMeeting") and (m.get("track") or {}).get("country") == "AUS"
                  and not m.get("isBarrierTrial") and not m.get("isJumps")]
    loc_order = {"M": 0, "P": 1, "C": 2}
    candidates.sort(key=lambda m: loc_order.get(m["track"].get("location"), 3))
    candidates = candidates[:14]
    if not candidates:
        return False

    meetings, races, runners = [], [], []
    for idx, m in enumerate(candidates):
        try:
            detail = await _get("form/fields", meetingId=m["meetingId"], raceNumber=0)
        except Exception as e:
            logger.warning(f"PF fields failed for {m['meetingId']}: {e}")
            continue
        pf_races = detail.get("races") or []
        if not pf_races:
            continue
        meeting_id = str(uuid.uuid4())
        meetings.append({
            "id": meeting_id, "pf_meeting_id": str(m["meetingId"]), "date": date_aest,
            "track": m["track"]["name"], "state": m["track"].get("state", ""),
            "condition": m.get("expectedCondition") or "TBA",
            "rail": m.get("railPosition") or "True",
            "races_count": len(pf_races), "feature": idx == 0, "source": "punting_form",
        })
        n_races = len(pf_races)
        for race in pf_races:
            race_id = str(uuid.uuid4())
            try:
                start = _parse_utc(race["startTimeUTC"])
            except Exception:
                start = datetime.now(AEST) + timedelta(hours=1)
            field = [r for r in (race.get("runners") or []) if not r.get("emergencyIndicator")]
            if not field:
                continue
            avg_wt = sum((r.get("weightTotal") or r.get("weight") or 57) for r in field) / len(field)
            scores = [_score_runner(r, avg_wt) for r in field]
            exps = [pow(2.718, s / 11) for s in scores]
            total = sum(exps)
            docs = []
            for i, r in enumerate(field):
                p = exps[i] / total
                rated = round(max(1.3, min(101.0, 0.92 / p)), 1)
                naive = (r.get("winPct") or 0) / 100.0
                market = round(max(1.3, min(101.0, 0.9 / max(0.02, naive))), 1) if naive > 0 else round(min(101.0, rated * 1.4), 1)
                docs.append({
                    "id": str(uuid.uuid4()), "race_id": race_id, "meeting_id": meeting_id,
                    "pf_runner_id": str(r.get("runnerId", "")),
                    "number": r.get("tabNo") or i + 1, "barrier": r.get("barrier") or 0,
                    "name": r.get("name", "Unknown"),
                    "jockey": (r.get("jockey") or {}).get("fullName", "").strip() or "TBA",
                    "trainer": (r.get("trainer") or {}).get("fullName", "").strip() or "TBA",
                    "weight": r.get("weightTotal") or r.get("weight") or 0,
                    "form": (r.get("last10") or "").strip()[-6:] or "-",
                    "win_prob": round(p, 4), "place_prob": round(min(0.96, p * 2.7), 4),
                    "odds_open": max(market, rated), "odds_current": rated,
                    "is_plunge": market > rated * 1.5 and p > 0.12, "scratched": False,
                })
            ranked = sorted(docs, key=lambda x: -x["win_prob"])
            for rank, d in enumerate(ranked):
                d["rank"] = rank + 1
                d["confidence"] = int(min(97, 42 + d["win_prob"] * 150 + (8 if rank == 0 else 0)))
                d["grade"] = "A" if (d["win_prob"] > 0.28 and d["confidence"] >= 84) else (
                    "B" if d["win_prob"] > 0.18 else "C")
                src = next(r for r in field if str(r.get("runnerId", "")) == d["pf_runner_id"])
                d["reasoning"] = _reasoning(src, rank, d["win_prob"])
            ranked[0]["aces_win"] = ranked[0]["win_prob"] > 0.24
            if len(ranked) > 1:
                ranked[1]["aces_place"] = ranked[1]["place_prob"] > 0.5
            races.append({
                "id": race_id, "meeting_id": meeting_id, "pf_race_id": str(race.get("raceId", "")),
                "number": race.get("number"), "name": race.get("name", ""),
                "distance": race.get("distance", 0), "start_aest": start.isoformat(),
                "status": "upcoming", "result": None,
                "is_quaddie_leg": idx == 0 and race.get("number", 0) > n_races - 4,
            })
            runners.extend(docs)

    if not races:
        return False
    await db.meetings.insert_many([{**x} for x in meetings])
    await db.races.insert_many([{**x} for x in races])
    await db.runners.insert_many([{**x} for x in runners])
    logger.info(f"Punting Form: loaded {len(meetings)} meetings / {len(races)} races for {date_aest}")
    return True


async def sync_results(db, date_aest: str):
    """Pull official results from PF and grade races that have finished."""
    meetings = await db.meetings.find({"date": date_aest, "source": "punting_form"}, {"_id": 0}).to_list(20)
    for m in meetings:
        pending = await db.races.find({"meeting_id": m["id"], "status": "upcoming"}, {"_id": 0}).to_list(20)
        started = [r for r in pending if datetime.fromisoformat(r["start_aest"]) < datetime.now(AEST)]
        if not started:
            continue
        try:
            payload = await _get("form/results", meetingId=m["pf_meeting_id"])
        except Exception as e:
            logger.warning(f"PF results failed for {m['pf_meeting_id']}: {e}")
            continue
        race_results = {}
        for entry in payload or []:
            for rr in entry.get("raceResults") or []:
                race_results[str(rr.get("raceId"))] = rr
        for race in started:
            rr = race_results.get(race.get("pf_race_id", ""))
            if not rr:
                continue
            placed = sorted([x for x in (rr.get("runners") or []) if x.get("position", 0) > 0],
                            key=lambda x: x["position"])
            if not placed or placed[0]["position"] != 1:
                continue
            positions = [x["tabNo"] for x in placed[:4]]
            rs = await db.runners.find({"race_id": race["id"]}, {"_id": 0}).to_list(50)
            top = min(rs, key=lambda x: x["rank"])
            win_price = placed[0].get("price") or 0
            if not win_price:
                win_r = next((x for x in rs if x["number"] == positions[0]), None)
                win_price = win_r["odds_current"] if win_r else 0
            cond = rr.get("trackConditionLabel")
            if cond and cond != "Unknown":
                await db.meetings.update_one({"id": m["id"]}, {"$set": {"condition": cond}})
            await db.races.update_one({"id": race["id"]}, {"$set": {
                "status": "resulted",
                "result": {"positions": positions, "win_dividend": round(float(win_price), 2),
                           "top_pick_won": top["number"] == positions[0],
                           "top_pick_placed": top["number"] in positions[:3]}}})

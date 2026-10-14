import random
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

AEST = ZoneInfo("Australia/Sydney")

TRACKS = [
    ("Randwick", "NSW"), ("Flemington", "VIC"), ("Eagle Farm", "QLD"),
    ("Morphettville", "SA"), ("Ascot", "WA"), ("Caulfield", "VIC"),
    ("Rosehill", "NSW"), ("Doomben", "QLD"),
]
CONDITIONS = ["Good 3", "Good 4", "Soft 5", "Soft 6", "Soft 7", "Heavy 8"]
JOCKEYS = ["J. McDonald", "C. Williams", "J. Kah", "N. Rawiller", "T. Berry", "D. Lane",
           "K. McEvoy", "B. Shinn", "R. King", "M. Zahra", "H. Coffey", "T. Nugent",
           "L. Currie", "W. Pike", "C. Schofield", "A. Hyeronimus"]
TRAINERS = ["C. Waller", "C. Maher", "G. Waterhouse & A. Bott", "J. O'Shea", "A. & S. Freedman",
            "T. Gollan", "P. Moody", "B. Baker", "M. Price & M. Kent Jnr", "K. Lees"]
NAME_A = ["Zou", "Deep", "Golden", "Midnight", "Royal", "Flying", "Savage", "Silent", "Turf",
          "Iron", "Crimson", "Southern", "Wild", "Lucky", "Storm", "Velvet", "Mighty", "Coastal",
          "Rebel", "Diamond", "Shadow", "Blazing", "Noble", "Outback"]
NAME_B = ["Warrior", "Impact", "Sizzle", "Empress", "Command", "Machine", "Legacy", "Assassin",
          "Monarch", "Dancer", "Rocket", "Star", "Fury", "Charm", "Baron", "Whisper", "Tycoon",
          "Comet", "Duchess", "Invader", "Sprint", "Glory", "Edge", "Anthem"]
DISTANCES = [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1800, 2000, 2400]
RACE_NAMES = ["Maiden Plate", "BM72 Handicap", "Class 3 Handicap", "Fillies & Mares BM78",
              "Open Handicap", "BM88 Handicap", "3YO Sprint", "Listed Stakes", "Group 3 Trophy",
              "Rating 64 Handicap"]

REASON_BITS = [
    "drawn to get a gun run from barrier {barrier}",
    "{jockey} boasts a strong strike rate at this track",
    "closed off powerfully last start with the fastest final 600m of the meeting",
    "second-up specialist with two wins from three attempts at this stage of prep",
    "wet-tracker who relishes give in the ground",
    "map king — should control the speed from the front",
    "trainer {trainer} has this yard firing at a 24% win clip this month",
    "big weight drop on last start against stronger opposition",
    "hit the line hard when resuming and strips fitter here",
    "class edge on this field having matched motors with stakes company",
    "significant market support since opening — stable confidence evident",
    "won this race last year off an identical preparation",
]


def _reason(runner, rank):
    bits = random.sample(REASON_BITS, 3)
    txt = "; ".join(b.format(**runner) for b in bits)
    lead = ["Top pick — ", "Strong claims — ", "Each-way value — ", "Knockout hope — "][min(rank, 3)]
    return (lead + txt + ".").replace("  ", " ")


def _form_string():
    return "".join(random.choice("1234567890x") for _ in range(5))


def seed_day(date_aest, now_aest):
    """Generate meetings/races/runners docs for a given AEST date."""
    rnd = random.Random(date_aest)
    meetings, races, runners = [], [], []
    tracks = rnd.sample(TRACKS, 5)
    for mi, (track, state) in enumerate(tracks):
        meeting_id = str(uuid.uuid4())
        n_races = rnd.randint(7, 9)
        meetings.append({
            "id": meeting_id, "date": date_aest, "track": track, "state": state,
            "location": "M" if mi < 3 else "P",
            "condition": rnd.choice(CONDITIONS), "rail": rnd.choice(["True", "+2m", "+4m", "+6m Entire"]),
            "races_count": n_races, "feature": mi == 0,
        })
        anchor = now_aest - timedelta(hours=3, minutes=10 - mi * 8)
        first = anchor.replace(minute=(anchor.minute // 5) * 5, second=0, microsecond=0)
        for rn in range(1, n_races + 1):
            race_id = str(uuid.uuid4())
            start = first + timedelta(minutes=42 * (rn - 1))
            n_run = rnd.randint(8, 12)
            ratings = [rnd.uniform(60, 100) for _ in range(n_run)]
            exps = [pow(2.718, r / 9) for r in ratings]
            total = sum(exps)
            race_runners = []
            for i in range(n_run):
                p = exps[i] / total
                cur = round(max(1.5, min(61.0, 0.9 / p + rnd.uniform(-0.3, 0.6))), 1)
                move = rnd.choices([1.0, 1.15, 0.9, 1.6, 2.1], weights=[50, 18, 18, 9, 5])[0]
                opened = round(min(81.0, cur * move), 1)
                runner = {
                    "id": str(uuid.uuid4()), "race_id": race_id, "meeting_id": meeting_id,
                    "number": i + 1, "barrier": 0, "name": "", "jockey": rnd.choice(JOCKEYS),
                    "trainer": rnd.choice(TRAINERS), "weight": round(rnd.uniform(53, 61), 1),
                    "form": _form_string(), "win_prob": round(p, 4),
                    "place_prob": round(min(0.96, p * 2.7), 4),
                    "odds_open": opened, "odds_current": cur,
                    "is_plunge": move >= 1.6, "scratched": False,
                }
                race_runners.append(runner)
            barriers = list(range(1, n_run + 1))
            rnd.shuffle(barriers)
            used = set()
            for i, r in enumerate(race_runners):
                r["barrier"] = barriers[i]
                while True:
                    nm = f"{rnd.choice(NAME_A)} {rnd.choice(NAME_B)}"
                    if nm not in used:
                        used.add(nm)
                        break
                r["name"] = nm
            ranked = sorted(race_runners, key=lambda x: -x["win_prob"])
            for rank, r in enumerate(ranked):
                r["rank"] = rank + 1
                r["confidence"] = int(min(97, 45 + r["win_prob"] * 140 + rnd.uniform(0, 8)))
                r["grade"] = "A" if (r["win_prob"] > 0.30 and r["confidence"] >= 85) else (
                    "B" if r["win_prob"] > 0.20 else "C")
                random.seed(r["id"])
                r["reasoning"] = _reason(r, rank)
            top = ranked[0]
            top["aces_win"] = top["win_prob"] > 0.26
            if len(ranked) > 1:
                ranked[1]["aces_place"] = ranked[1]["place_prob"] > 0.55
            race = {
                "id": race_id, "meeting_id": meeting_id, "number": rn,
                "name": rnd.choice(RACE_NAMES), "distance": rnd.choice(DISTANCES),
                "start_aest": start.isoformat(), "status": "upcoming", "result": None,
                "is_quaddie_leg": meetings[-1]["feature"] and rn > n_races - 4,
            }
            if start < now_aest:
                probs = [r["win_prob"] for r in race_runners]
                order = []
                pool = list(range(n_run))
                w = probs[:]
                for _ in range(4):
                    pick = rnd.choices(pool, weights=[w[j] for j in pool])[0]
                    order.append(race_runners[pick]["number"])
                    pool.remove(pick)
                win_r = next(x for x in race_runners if x["number"] == order[0])
                race["status"] = "resulted"
                race["result"] = {
                    "positions": order,
                    "win_dividend": round(win_r["odds_current"], 2),
                    "top_pick_won": top["number"] == order[0],
                    "top_pick_placed": top["number"] in order[:3],
                }
            races.append(race)
            runners.extend(race_runners)
    return meetings, races, runners


def build_exotics(race_runners):
    top = sorted([r for r in race_runners if not r["scratched"]], key=lambda x: x["rank"])[:5]
    n = [r["number"] for r in top]
    nm = {r["number"]: r["name"] for r in top}
    def label(nums):
        return " / ".join(f"{x}. {nm[x]}" for x in nums)
    return [
        {"type": "Exacta (Standout)", "combo": f"{n[0]} to beat {n[1]}, {n[2]}", "runners": label(n[:3]),
         "cost_per_unit": 2.0, "est_return": round(top[0]["odds_current"] * top[1]["odds_current"] * 0.42, 2)},
        {"type": "Quinella (Box 3)", "combo": f"Box {n[0]}, {n[1]}, {n[2]}", "runners": label(n[:3]),
         "cost_per_unit": 3.0, "est_return": round(top[0]["odds_current"] * top[1]["odds_current"] * 0.3, 2)},
        {"type": "Trifecta (Box 4)", "combo": f"Box {n[0]}, {n[1]}, {n[2]}, {n[3]}", "runners": label(n[:4]),
         "cost_per_unit": 24.0, "est_return": round(top[0]["odds_current"] * top[1]["odds_current"] * top[2]["odds_current"] * 0.55, 2)},
        {"type": "First Four (Box 5)", "combo": f"Box {', '.join(map(str, n[:5]))}", "runners": label(n[:5]),
         "cost_per_unit": 120.0, "est_return": round(top[0]["odds_current"] * top[1]["odds_current"] * top[2]["odds_current"] * top[3]["odds_current"] * 0.4, 2)},
    ]

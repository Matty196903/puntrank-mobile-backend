from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

EMERALD = colors.HexColor("#10B981")
GOLD = colors.HexColor("#F59E0B")
DARK = colors.HexColor("#0A0D0E")

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Title"], textColor=DARK, fontSize=20, spaceAfter=4)
SUB = ParagraphStyle("SUB", parent=styles["Normal"], textColor=colors.HexColor("#555"), fontSize=9, spaceAfter=12)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=EMERALD, fontSize=13)
BODY = ParagraphStyle("BODY", parent=styles["Normal"], fontSize=9)
FOOT = ParagraphStyle("FOOT", parent=styles["Normal"], fontSize=7, textColor=colors.grey)

DISCLAIMER = ("PuntRank Aus is a probability-ranking tool, not a betting service. 18+ only. Gamble responsibly. "
              "Chances are you're about to lose. Call 1800 858 858 or visit gamblinghelponline.org.au")

TBL_STYLE = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), DARK),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCC")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F7F5")]),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
])


def _doc(title, date):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=36, bottomMargin=36)
    story = [Paragraph(f"PuntRank Aus — {title}", H1),
             Paragraph(f"{date} • Australian Eastern Time • Ace's 60-Year Selection System", SUB)]
    return buf, doc, story


def _finish(buf, doc, story):
    story.append(Spacer(1, 18))
    story.append(Paragraph(DISCLAIMER, FOOT))
    doc.build(story)
    buf.seek(0)
    return buf.read()


def form_guide_pdf(date, meetings, races, runners_by_race):
    buf, doc, story = _doc("Form Guide", date)
    for m in meetings:
        story.append(Paragraph(f"{m['track']} ({m['state']}) — {m['condition']}, Rail {m['rail']}", H2))
        for race in [r for r in races if r["meeting_id"] == m["id"]][:4]:
            story.append(Paragraph(f"Race {race['number']} — {race['name']} ({race['distance']}m)", BODY))
            rows = [["#", "Horse", "Jockey", "Bar", "Win %", "Place %", "Odds", "Grade"]]
            for r in sorted(runners_by_race.get(race["id"], []), key=lambda x: x["rank"])[:6]:
                rows.append([r["number"], r["name"], r["jockey"], r["barrier"],
                             f"{r['win_prob']*100:.0f}%", f"{r['place_prob']*100:.0f}%",
                             f"${r['odds_current']}", r["grade"]])
            t = Table(rows, colWidths=[24, 120, 90, 30, 44, 48, 44, 40])
            t.setStyle(TBL_STYLE)
            story.append(t)
            story.append(Spacer(1, 8))
    return _finish(buf, doc, story)


def results_wrap_pdf(date, meetings, resulted, runners_by_race):
    buf, doc, story = _doc("Results Wrap", date)
    mmap = {m["id"]: m for m in meetings}
    rows = [["Track", "Race", "Winner", "Div", "Top Pick Result"]]
    for race in resulted:
        rmap = {r["number"]: r for r in runners_by_race.get(race["id"], [])}
        win = rmap.get(race["result"]["positions"][0])
        rows.append([mmap[race["meeting_id"]]["track"], f"R{race['number']}",
                     f"{win['number']}. {win['name']}" if win else "-",
                     f"${race['result']['win_dividend']}",
                     "WON" if race["result"]["top_pick_won"] else ("PLACED" if race["result"]["top_pick_placed"] else "Unplaced")])
    t = Table(rows, colWidths=[100, 40, 160, 50, 90])
    t.setStyle(TBL_STYLE)
    story.append(t)
    wins = sum(1 for r in resulted if r["result"]["top_pick_won"])
    places = sum(1 for r in resulted if r["result"]["top_pick_placed"])
    n = max(1, len(resulted))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Daily strike rate: {wins}/{len(resulted)} winners ({wins/n*100:.0f}%) • {places}/{len(resulted)} placed ({places/n*100:.0f}%)", H2))
    return _finish(buf, doc, story)


def top10_pdf(date, picks, mmap, races_map):
    buf, doc, story = _doc("Ace's Top 10 Picks", date)
    rows = [["Rank", "Horse", "Track / Race", "Win %", "Odds", "Confidence", "Grade"]]
    for i, r in enumerate(picks[:10], 1):
        race = races_map[r["race_id"]]
        rows.append([i, f"{r['number']}. {r['name']}",
                     f"{mmap[r['meeting_id']]['track']} R{race['number']}",
                     f"{r['win_prob']*100:.0f}%", f"${r['odds_current']}", r["confidence"], r["grade"]])
    t = Table(rows, colWidths=[34, 140, 130, 46, 46, 62, 40])
    t.setStyle(TBL_STYLE)
    story.append(t)
    return _finish(buf, doc, story)


def quaddie_pdf(date, track, legs):
    buf, doc, story = _doc(f"Ace's Quaddie — {track}", date)
    total = 1
    for leg in legs:
        story.append(Paragraph(f"Leg {leg['leg']} — Race {leg['race_number']} ({leg['distance']}m)", H2))
        rows = [["#", "Horse", "Win %", "Odds"]]
        for r in leg["selections"]:
            rows.append([r["number"], r["name"], f"{r['win_prob']*100:.0f}%", f"${r['odds_current']}"])
        total *= len(leg["selections"])
        t = Table(rows, colWidths=[30, 180, 60, 60])
        t.setStyle(TBL_STYLE)
        story.append(t)
        story.append(Spacer(1, 8))
    story.append(Paragraph(f"Combinations: {total} — 100% unit cost ${total:.2f} / 50% flexi ${total/2:.2f}", H2))
    return _finish(buf, doc, story)


def staking_pdf(date):
    buf, doc, story = _doc("Staking Calculator", date)
    story.append(Paragraph("Recommended unit staking by confidence band (1 unit = 1% of bank)", H2))
    rows = [["Confidence", "Grade", "Win Stake", "Place Stake", "Notes"],
            ["90+", "A", "3 units", "2 units", "Strongest bets of the day"],
            ["80-89", "A/B", "2 units", "1.5 units", "Solid win chances"],
            ["70-79", "B", "1 unit", "1 unit", "Each-way value"],
            ["60-69", "C", "0.5 units", "1 unit", "Place focus / exotics anchor"],
            ["<60", "C", "No bet", "0.5 units", "Exotics roughie only"]]
    t = Table(rows, colWidths=[70, 50, 80, 80, 190])
    t.setStyle(TBL_STYLE)
    story.append(t)
    story.append(Spacer(1, 10))
    story.append(Paragraph("Never chase losses. Set a daily limit before racing begins and stop when it is reached.", BODY))
    return _finish(buf, doc, story)


def scorecard_pdf(date, resulted, mmap):
    buf, doc, story = _doc("A-Grade Scorecard", date)
    rows = [["Track", "Race", "Result", "Units +/-"]]
    bank = 0.0
    for race in resulted:
        res = race["result"]
        if res["top_pick_won"]:
            delta = round(res["win_dividend"] - 1, 2)
        elif res["top_pick_placed"]:
            delta = round(res["win_dividend"] * 0.3 - 1, 2)
        else:
            delta = -1.0
        bank += delta
        rows.append([mmap[race["meeting_id"]]["track"], f"R{race['number']}",
                     "WIN" if res["top_pick_won"] else ("PLACE" if res["top_pick_placed"] else "LOSS"),
                     f"{delta:+.2f}"])
    rows.append(["", "", "TOTAL", f"{bank:+.2f}"])
    t = Table(rows, colWidths=[140, 60, 100, 80])
    t.setStyle(TBL_STYLE)
    story.append(t)
    return _finish(buf, doc, story)

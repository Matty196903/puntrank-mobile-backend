import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Ticket, Trophy, ChevronRight } from "lucide-react";
import api from "@/lib/api";
import { ProLock } from "@/components/ProLock";
import { fmtAest } from "@/lib/time";

export default function ExoticsPage() {
  const [bb, setBb] = useState(null);
  const [meetings, setMeetings] = useState([]);
  const [meetingId, setMeetingId] = useState("");
  const [races, setRaces] = useState([]);
  const [raceId, setRaceId] = useState("");
  const [exotics, setExotics] = useState(null);

  useEffect(() => {
    api.get("/best-bets").then((r) => setBb(r.data));
    api.get("/meetings").then((r) => {
      setMeetings(r.data.meetings);
      if (r.data.meetings[0]) setMeetingId(r.data.meetings[0].id);
    });
  }, []);

  useEffect(() => {
    if (!meetingId) return;
    api.get(`/meetings/${meetingId}/races`).then((r) => {
      setRaces(r.data.races);
      setRaceId(r.data.races[0]?.id || "");
    });
  }, [meetingId]);

  useEffect(() => {
    if (!raceId) { setExotics(null); return; }
    api.get(`/races/${raceId}/exotics`).then((r) => setExotics(r.data));
  }, [raceId]);

  return (
    <div className="fade-up" data-testid="exotics-page">
      <div className="flex items-center gap-2">
        <Ticket className="w-6 h-6 text-amber-500" />
        <h1 className="font-display text-4xl font-extrabold uppercase tracking-tight">Exotics</h1>
      </div>
      <p className="text-sm text-zinc-400 mt-1 mb-4">Exacta, quinella, trifecta, first four & quaddie combinations built from the rankings.</p>

      <Link to="/aces" data-testid="exotics-aces-link" className="pr-card p-4 flex items-center gap-3 mb-5 group border-amber-500/25">
        <Trophy className="w-5 h-5 text-amber-400 shrink-0" />
        <div className="flex-1">
          <p className="font-display text-lg font-bold uppercase">Ace's Exotics</p>
          <p className="text-xs text-zinc-500">Winners, Places & today's Quaddie</p>
        </div>
        <ChevronRight className="w-5 h-5 text-zinc-600 group-hover:text-amber-400 transition-colors" />
      </Link>

      <h2 className="font-display text-2xl font-bold uppercase tracking-tight mb-2">Race Exotics</h2>
      <div className="grid grid-cols-2 gap-2 mb-3">
        <select data-testid="exotics-meeting-select" value={meetingId} onChange={(e) => setMeetingId(e.target.value)}
          className="bg-[#121719] border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-200">
          {meetings.map((m) => <option key={m.id} value={m.id}>{m.track}</option>)}
        </select>
        <select data-testid="exotics-race-select" value={raceId} onChange={(e) => setRaceId(e.target.value)}
          className="bg-[#121719] border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-200">
          {races.map((r) => <option key={r.id} value={r.id}>R{r.number} · {fmtAest(r.start_aest)}</option>)}
        </select>
      </div>

      {exotics && (
        <div className="space-y-2.5 mb-2">
          {exotics.exotics.map((x, i) => (
            <div key={i} className="pr-card p-4" data-testid={`exotic-card-${i}`}>
              <div className="flex items-center justify-between">
                <p className="font-display text-lg font-bold uppercase text-emerald-400">{x.type}</p>
                <p className="font-mono-num text-xs text-zinc-400">Unit ${x.cost_per_unit} · Est ${x.est_return}</p>
              </div>
              <p className="text-sm text-zinc-300 mt-1">{x.combo}</p>
              <p className="text-xs text-zinc-500 mt-0.5">{x.runners}</p>
            </div>
          ))}
          {exotics.locked > 0 && <ProLock count={exotics.locked} label="exotic combinations" testid="exotics-pro-lock" />}
        </div>
      )}

      {bb && (
        <>
          <h2 className="font-display text-2xl font-bold uppercase tracking-tight mt-6 mb-2">Best-Bet Shortlist</h2>
          <div className="space-y-2">
            {bb.bets.slice(0, 5).map((b) => (
              <div key={b.id} className="pr-card p-3 flex items-center justify-between" data-testid={`shortlist-${b.id}`}>
                <div>
                  <p className="font-semibold text-sm">{b.number}. {b.name}</p>
                  <p className="text-xs text-zinc-500">{b.track} R{b.race_number} · {fmtAest(b.start_aest)}</p>
                </div>
                <p className="font-mono-num text-emerald-400 font-bold">${b.odds_current}</p>
              </div>
            ))}
          </div>
          {bb.multis.length > 0 && (
            <>
              <h2 className="font-display text-2xl font-bold uppercase tracking-tight mt-6 mb-2">Cross-Race Multis</h2>
              <div className="space-y-2.5">
                {bb.multis.map((m, i) => (
                  <div key={i} className="pr-card p-4 border-amber-500/25" data-testid={`exotics-multi-${i}`}>
                    <div className="flex items-center justify-between">
                      <p className="font-display text-lg font-bold uppercase text-amber-400">{m.name}</p>
                      <p className="font-mono-num font-bold text-amber-400">${m.combined_odds}</p>
                    </div>
                    <div className="mt-1.5 space-y-0.5">
                      {m.legs.map((l) => (
                        <p key={l.id} className="text-xs text-zinc-400">{l.track} R{l.race_number}: {l.number}. {l.name} <span className="font-mono-num text-zinc-300">${l.odds_current}</span></p>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
          {bb.locked > 0 && <div className="mt-3"><ProLock count={bb.locked} label="shortlist bets" testid="exotics-bb-lock" /></div>}
        </>
      )}
    </div>
  );
}

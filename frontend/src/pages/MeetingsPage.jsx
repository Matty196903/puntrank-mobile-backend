import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import dayjs from "dayjs";
import { MapPin, ChevronRight, Flag, Share2 } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { fmtAest } from "@/lib/time";

const COND_COLOR = (c) => c.startsWith("Good") ? "bg-emerald-500/15 text-emerald-400" : c.startsWith("Soft") ? "bg-amber-500/15 text-amber-400" : c.startsWith("Heavy") ? "bg-red-500/15 text-red-400" : "bg-zinc-700/40 text-zinc-300";

export default function MeetingsPage() {
  const [data, setData] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.get("/meetings").then((r) => setData(r.data));
    api.get("/results").then((r) => setStats(r.data.stats));
  }, []);

  if (!data) return <p className="text-zinc-500 text-sm py-10 text-center" data-testid="meetings-loading">Loading today's meetings…</p>;

  const share = async () => {
    let pickLine = "";
    try {
      const { data: bb } = await api.get("/best-bets");
      const top = bb.bets[0];
      if (top) pickLine = `Today's top pick: ${top.number}. ${top.name} (${top.track} R${top.race_number}) @ $${top.odds_current}. `;
    } catch { /* share without pick */ }
    const text = `🏇 PuntRank Aus — Australia's racing form ranker. ${pickLine}See how it works: ${window.location.origin}/guide (18+ only, gamble responsibly)`;
    if (navigator.share) {
      try { await navigator.share({ title: "PuntRank Aus", text, url: `${window.location.origin}/guide` }); return; } catch { return; }
    }
    await navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard", { description: "Paste it to your mates 🏇" });
  };

  return (
    <div className="fade-up" data-testid="meetings-page">
      <div className="mb-5 flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-bold text-amber-500 uppercase tracking-widest">Australian Eastern Time</p>
          <h1 className="font-display text-4xl font-extrabold uppercase tracking-tight mt-1">
            Today's Meetings
          </h1>
          <p className="text-sm text-zinc-400 mt-1">{dayjs(data.date_aest).format("dddd D MMMM YYYY")} · Ranked by Ace's 60-year system</p>
        </div>
        <button data-testid="share-btn" onClick={share}
          className="shrink-0 mt-1 flex items-center gap-1.5 px-3 py-2 rounded-full border border-zinc-700 text-zinc-300 text-xs font-semibold hover:border-emerald-500/60 hover:text-emerald-400 transition-colors">
          <Share2 className="w-4 h-4" /> Share
        </button>
      </div>

      {(() => {
        const jumps = data.meetings.filter((m) => m.next_race).sort((a, b) => a.next_race.start_aest.localeCompare(b.next_race.start_aest)).slice(0, 6);
        return jumps.length > 0 && (
          <div className="mb-5" data-testid="next-to-jump">
            <p className="text-xs font-bold text-emerald-500 uppercase tracking-widest mb-2">Next to Jump</p>
            <div className="flex gap-2 overflow-x-auto pb-1 -mx-4 px-4">
              {jumps.map((m) => (
                <Link key={m.id} to={`/meeting/${m.id}`} data-testid={`jump-chip-${m.id}`}
                  className="shrink-0 pr-card px-3 py-2 flex items-center gap-2 border-emerald-500/20">
                  <span className="font-display font-bold uppercase text-sm">{m.track}</span>
                  <span className="text-xs text-emerald-400 font-semibold">R{m.next_race.number}</span>
                  <span className="font-mono-num text-xs text-zinc-400">{fmtAest(m.next_race.start_aest)}</span>
                </Link>
              ))}
            </div>
          </div>
        );
      })()}

      <div className="grid grid-cols-2 gap-2 mb-5">
        <Link to="/aces" data-testid="home-aces-card" className="pr-card p-3.5 border-amber-500/25 group">
          <p className="font-display text-lg font-bold uppercase text-amber-400">Ace's Exotics</p>
          <p className="text-[11px] text-zinc-500 mt-0.5">Winners · Places · Quaddie</p>
        </Link>
        <Link to="/best-bets" data-testid="home-agrade-card" className="pr-card p-3.5 border-emerald-500/25 group">
          <p className="font-display text-lg font-bold uppercase text-emerald-400">A-Grade Plays</p>
          <p className="text-[11px] text-zinc-500 mt-0.5">Strongest bets, graded live</p>
        </Link>
      </div>

      {stats && stats.resulted > 0 && (
        <div className="grid grid-cols-3 gap-2 mb-5">
          <div className="pr-card p-3 text-center"><p className="font-mono-num text-xl font-bold text-emerald-400" data-testid="stat-win-strike">{stats.win_strike}%</p><p className="text-[11px] text-zinc-500">Win strike</p></div>
          <div className="pr-card p-3 text-center"><p className="font-mono-num text-xl font-bold text-blue-400">{stats.place_strike}%</p><p className="text-[11px] text-zinc-500">Place strike</p></div>
          <div className="pr-card p-3 text-center"><p className="font-mono-num text-xl font-bold text-zinc-200">{stats.resulted}</p><p className="text-[11px] text-zinc-500">Races graded</p></div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {data.meetings.map((m) => (
          <Link key={m.id} to={`/meeting/${m.id}`} data-testid={`meeting-card-${m.id}`} className="pr-card p-4 flex items-center gap-3 group">
            <div className="w-11 h-11 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0">
              <Flag className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="font-display text-xl font-bold uppercase truncate">{m.track}</p>
                {m.feature && <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400">FEATURE</span>}
              </div>
              <div className="flex items-center gap-2 mt-1 text-xs text-zinc-500">
                <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{m.state}</span>
                <span className={`px-1.5 py-0.5 rounded font-semibold ${COND_COLOR(m.condition)}`}>{m.condition}</span>
                <span>Rail {m.rail}</span>
              </div>
              <p className="text-xs text-zinc-400 mt-1.5">
                {m.resulted}/{m.races_count} run
                {m.next_race && <> · Next R{m.next_race.number} at {fmtAest(m.next_race.start_aest)}</>}
              </p>
            </div>
            <ChevronRight className="w-5 h-5 text-zinc-600 group-hover:text-emerald-400 transition-colors" />
          </Link>
        ))}
      </div>
    </div>
  );
}

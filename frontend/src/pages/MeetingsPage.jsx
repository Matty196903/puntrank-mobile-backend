import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import dayjs from "dayjs";
import { MapPin, ChevronRight, Flag } from "lucide-react";
import api from "@/lib/api";

const COND_COLOR = (c) => c.startsWith("Good") ? "bg-emerald-500/15 text-emerald-400" : c.startsWith("Soft") ? "bg-amber-500/15 text-amber-400" : "bg-red-500/15 text-red-400";

export default function MeetingsPage() {
  const [data, setData] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.get("/meetings").then((r) => setData(r.data));
    api.get("/results").then((r) => setStats(r.data.stats));
  }, []);

  if (!data) return <p className="text-zinc-500 text-sm py-10 text-center" data-testid="meetings-loading">Loading today's meetings…</p>;

  return (
    <div className="fade-up" data-testid="meetings-page">
      <div className="mb-5">
        <p className="text-xs font-bold text-amber-500 uppercase tracking-widest">Australian Eastern Time</p>
        <h1 className="font-display text-4xl font-extrabold uppercase tracking-tight mt-1">
          Today's Meetings
        </h1>
        <p className="text-sm text-zinc-400 mt-1">{dayjs(data.date_aest).format("dddd D MMMM YYYY")} · Ranked by Ace's 60-year system</p>
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
                {m.next_race && <> · Next R{m.next_race.number} at {dayjs(m.next_race.start_aest).format("h:mm A")}</>}
              </p>
            </div>
            <ChevronRight className="w-5 h-5 text-zinc-600 group-hover:text-emerald-400 transition-colors" />
          </Link>
        ))}
      </div>
    </div>
  );
}

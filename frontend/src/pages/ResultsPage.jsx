import { useEffect, useState } from "react";
import { BarChart3 } from "lucide-react";
import api from "@/lib/api";
import { fmtAest } from "@/lib/time";

export default function ResultsPage() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/results").then((r) => setData(r.data)); }, []);
  if (!data) return <p className="text-zinc-500 text-sm py-10 text-center">Loading results…</p>;
  const s = data.stats;

  return (
    <div className="fade-up" data-testid="results-page">
      <div className="flex items-center gap-2">
        <BarChart3 className="w-6 h-6 text-emerald-500" />
        <h1 className="font-display text-4xl font-extrabold uppercase tracking-tight">Results</h1>
      </div>
      <p className="text-sm text-zinc-400 mt-1 mb-4">Every resulted race graded against Ace's top pick.</p>

      <div className="grid grid-cols-3 gap-2 mb-5">
        <div className="pr-card p-3 text-center"><p className="font-mono-num text-xl font-bold text-emerald-400" data-testid="results-win-strike">{s.win_strike}%</p><p className="text-[11px] text-zinc-500">Win strike ({s.wins}/{s.resulted})</p></div>
        <div className="pr-card p-3 text-center"><p className="font-mono-num text-xl font-bold text-blue-400">{s.place_strike}%</p><p className="text-[11px] text-zinc-500">Place strike ({s.places}/{s.resulted})</p></div>
        <div className="pr-card p-3 text-center"><p className="font-mono-num text-xl font-bold text-zinc-200">{s.resulted}</p><p className="text-[11px] text-zinc-500">Races graded</p></div>
      </div>

      <div className="space-y-2.5">
        {data.results.map((r) => (
          <div key={r.race_id} className="pr-card p-4" data-testid={`result-${r.race_id}`}>
            <div className="flex items-center justify-between">
              <p className="font-semibold text-sm">{r.track} R{r.race_number} — {r.name}</p>
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${r.top_pick_won ? "bg-emerald-500/20 text-emerald-400" : r.top_pick_placed ? "bg-blue-500/20 text-blue-400" : "bg-zinc-700/40 text-zinc-400"}`}>
                {r.top_pick_won ? "TOP PICK WON" : r.top_pick_placed ? "TOP PICK PLACED" : "UNPLACED"}
              </span>
            </div>
            <p className="text-xs text-zinc-500">{r.distance}m · {fmtAest(r.start_aest)} · Pick: {r.top_pick.number}. {r.top_pick.name}</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {r.placings.map((p) => (
                <span key={p.pos} className={`text-xs px-2 py-1 rounded-lg border ${p.pos === 1 ? "border-amber-500/40 bg-amber-500/10 text-amber-300" : "border-zinc-800 text-zinc-400"}`}>
                  {p.pos}. {p.number} {p.name}{p.pos === 1 && <span className="font-mono-num ml-1">${p.odds}</span>}
                </span>
              ))}
            </div>
          </div>
        ))}
        {data.results.length === 0 && <p className="text-sm text-zinc-500 py-8 text-center">No races resulted yet — check back after the first race jumps.</p>}
      </div>
    </div>
  );
}

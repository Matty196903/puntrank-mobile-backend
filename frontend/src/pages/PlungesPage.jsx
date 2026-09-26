import { useEffect, useState } from "react";
import { TrendingDown, ArrowRight } from "lucide-react";
import api from "@/lib/api";
import { fmtAest } from "@/lib/time";

export default function PlungesPage() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/movers").then((r) => setData(r.data)); }, []);
  if (!data) return <p className="text-zinc-500 text-sm py-10 text-center">Scanning the markets…</p>;

  return (
    <div className="fade-up" data-testid="plunges-page">
      <div className="flex items-center gap-2">
        <TrendingDown className="w-6 h-6 text-red-500" />
        <h1 className="font-display text-4xl font-extrabold uppercase tracking-tight">Market Movers</h1>
      </div>
      <p className="text-sm text-zinc-400 mt-1 mb-4">Significant firmers since markets opened — where the smart money is landing.</p>
      <div className="space-y-2.5">
        {data.movers.map((m) => (
          <div key={m.id} className={`pr-card p-4 ${m.move_pct >= 35 ? "plunge-pulse border-red-500/50" : ""}`} data-testid={`mover-${m.id}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-semibold text-sm">{m.number}. {m.name}</p>
                  {m.move_pct >= 35 && <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-500/20 text-red-400">PLUNGE</span>}
                </div>
                <p className="text-xs text-zinc-500">{m.track} R{m.race_number} · {fmtAest(m.start_aest)} · {m.jockey}</p>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-1.5 justify-end font-mono-num text-sm">
                  <span className="text-zinc-500 line-through">${m.odds_open}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-red-400" />
                  <span className="text-emerald-400 font-bold">${m.odds_current}</span>
                </div>
                <p className="text-[11px] font-bold text-red-400">-{m.move_pct}%</p>
              </div>
            </div>
          </div>
        ))}
        {data.movers.length === 0 && <p className="text-sm text-zinc-500 py-8 text-center">No significant market moves yet today.</p>}
      </div>
    </div>
  );
}

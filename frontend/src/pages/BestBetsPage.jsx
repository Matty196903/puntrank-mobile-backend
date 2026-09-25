import { useEffect, useState } from "react";
import dayjs from "dayjs";
import { Crown } from "lucide-react";
import api from "@/lib/api";
import { ProLock } from "@/components/ProLock";

export default function BestBetsPage() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/best-bets").then((r) => setData(r.data)); }, []);
  if (!data) return <p className="text-zinc-500 text-sm py-10 text-center">Loading A-Grade bets…</p>;

  return (
    <div className="fade-up" data-testid="best-bets-page">
      <div className="flex items-center gap-2">
        <Crown className="w-6 h-6 text-amber-500" />
        <h1 className="font-display text-4xl font-extrabold uppercase tracking-tight">A-Grade Bets</h1>
      </div>
      <p className="text-sm text-zinc-400 mt-1 mb-4">Strongest bets of the day, graded live against results.</p>

      <div className="space-y-2.5">
        {data.bets.map((b) => (
          <div key={b.id} className="pr-card p-4" data-testid={`best-bet-${b.id}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-semibold text-sm">{b.number}. {b.name}</p>
                  {b.graded && (
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${b.graded === "WON" ? "bg-emerald-500/20 text-emerald-400" : b.graded === "PLACED" ? "bg-blue-500/20 text-blue-400" : "bg-zinc-700/40 text-zinc-400"}`} data-testid={`best-bet-graded-${b.id}`}>{b.graded}</span>
                  )}
                  {!b.graded && <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400">LIVE</span>}
                </div>
                <p className="text-xs text-zinc-500">{b.track} R{b.race_number} · {dayjs(b.start_aest).format("h:mm A")} · {b.jockey}</p>
              </div>
              <div className="text-right">
                <p className="font-mono-num text-emerald-400 font-bold">${b.odds_current}</p>
                <p className="text-[11px] text-zinc-500">Conf {b.confidence}/100</p>
              </div>
            </div>
            <div className="prob-bar mt-2.5"><div style={{ width: `${Math.min(100, b.win_prob * 220)}%` }} /></div>
          </div>
        ))}
      </div>

      {data.locked > 0 && <div className="mt-3"><ProLock count={data.locked} label="A-Grade bets" testid="best-bets-pro-lock" /></div>}

      {data.multis.length > 0 && (
        <div className="mt-6">
          <h2 className="font-display text-2xl font-bold uppercase tracking-tight mb-2">Cross-Race Multis</h2>
          <div className="space-y-2.5">
            {data.multis.map((m, i) => (
              <div key={i} className="pr-card p-4 border-amber-500/25" data-testid={`multi-card-${i}`}>
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
        </div>
      )}
    </div>
  );
}

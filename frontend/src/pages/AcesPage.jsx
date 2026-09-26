import { useEffect, useState } from "react";
import { Trophy } from "lucide-react";
import api from "@/lib/api";
import { ProLock } from "@/components/ProLock";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { fmtAest } from "@/lib/time";

const PickCard = ({ r, kind }) => {
  const res = r.result;
  const graded = res ? (r.number === res.positions[0] ? "WON" : res.positions.slice(0, 3).includes(r.number) ? "PLACED" : "UNPLACED") : null;
  return (
    <div className="pr-card p-4" data-testid={`aces-pick-${r.id}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="font-semibold text-sm">{r.number}. {r.name}</p>
          <p className="text-xs text-zinc-500">{r.track} R{r.race_number} · {fmtAest(r.start_aest)} · {r.jockey}</p>
        </div>
        <div className="text-right">
          <p className="font-mono-num text-emerald-400 font-bold">${r.odds_current}</p>
          <p className="text-[11px] text-zinc-500">{kind === "place" ? `Pl ${(r.place_prob * 100).toFixed(0)}%` : `Win ${(r.win_prob * 100).toFixed(0)}%`}</p>
        </div>
      </div>
      {graded && (
        <span className={`inline-block mt-2 text-[10px] font-bold px-2 py-0.5 rounded ${graded === "WON" ? "bg-emerald-500/20 text-emerald-400" : graded === "PLACED" ? "bg-blue-500/20 text-blue-400" : "bg-zinc-700/40 text-zinc-400"}`}>{graded}</span>
      )}
    </div>
  );
};

export default function AcesPage() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/selections/aces").then((r) => setData(r.data)); }, []);
  if (!data) return <p className="text-zinc-500 text-sm py-10 text-center">Loading Ace's selections…</p>;

  return (
    <div className="fade-up" data-testid="aces-page">
      <div className="flex items-center gap-2">
        <Trophy className="w-6 h-6 text-amber-500" />
        <h1 className="font-display text-4xl font-extrabold uppercase tracking-tight">Ace's Selections</h1>
      </div>
      <p className="text-sm text-zinc-400 mt-1 mb-4">60 years of form craft distilled into today's Winners, Places and Quaddies.</p>

      <Tabs defaultValue="winners">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="winners" data-testid="tab-winners">Winners</TabsTrigger>
          <TabsTrigger value="places" data-testid="tab-places">Places</TabsTrigger>
          <TabsTrigger value="quaddie" data-testid="tab-quaddie">Quaddie</TabsTrigger>
        </TabsList>
        <TabsContent value="winners" className="space-y-2.5 mt-3">
          {data.winners.map((r) => <PickCard key={r.id} r={r} kind="win" />)}
          {!data.pro && <ProLock count={0} label="Every Ace's winner unlocked with Pro" testid="winners-pro-lock" />}
        </TabsContent>
        <TabsContent value="places" className="space-y-2.5 mt-3">
          {data.places.map((r) => <PickCard key={r.id} r={r} kind="place" />)}
          {!data.pro && <ProLock count={0} label="All place selections unlocked with Pro" testid="places-pro-lock" />}
        </TabsContent>
        <TabsContent value="quaddie" className="space-y-2.5 mt-3">
          {data.pro ? (
            <>
              {data.quaddie_track && <p className="text-sm text-zinc-300 font-semibold">Feature quaddie — {data.quaddie_track}</p>}
              {data.quaddie.map((leg) => (
                <div key={leg.leg} className="pr-card p-4" data-testid={`quaddie-leg-${leg.leg}`}>
                  <p className="font-display text-lg font-bold uppercase text-emerald-400">Leg {leg.leg} — Race {leg.race_number}</p>
                  <p className="text-xs text-zinc-500">{leg.distance}m · {fmtAest(leg.start_aest)}</p>
                  <div className="mt-2 space-y-1">
                    {leg.selections.map((s) => (
                      <div key={s.id} className="flex justify-between text-sm">
                        <span>{s.number}. {s.name}</span>
                        <span className="font-mono-num text-emerald-400">${s.odds_current}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </>
          ) : (
            <ProLock count={4} label="quaddie legs" testid="quaddie-pro-lock" />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
